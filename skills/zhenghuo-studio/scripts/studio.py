"""Local planning and handoff utilities. No media generation or paid API calls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, HTTPRedirectHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ('original', 'multi-reference', 'adaptation', 'precise')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')

def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def number(value, label, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{label}: 必须是有限数值')
    if value < 0 or (positive and value == 0):
        raise ValueError(f'{label}: 必须为' + ('正数' if positive else '非负数'))
    return float(value)

def validate(plan, base):
    if plan.get('schema_version') != '1.0': raise ValueError('不支持的 schema_version')
    if plan.get('route') not in ROUTES: raise ValueError('未知路线')
    for field in ('project_id', 'market', 'language'):
        if not isinstance(plan.get(field), str) or not plan[field].strip(): raise ValueError(f'缺少 {field}')
    target = number(plan.get('target_duration_sec'), '目标时长', True)
    capabilities = plan.get('video_profile', {})
    if capabilities.get('backend') != 'h3-api': raise ValueError('本工具箱视频交接必须明确使用 h3-api')
    if plan.get('image_backend') != 'local': raise ValueError('本工具箱图片交接必须使用 local')
    allowed = capabilities.get('allowed_durations_sec')
    if not isinstance(allowed, list) or not allowed: raise ValueError('缺少已核实的允许生成时长')
    allowed = [number(x, '允许生成时长', True) for x in allowed]
    for field in ('provider', 'model', 'resolution', 'evidence', 'verified_at'):
        if not isinstance(capabilities.get(field), str) or not capabilities[field].strip():
            raise ValueError(f'video_profile 缺少 {field}')
    segments = plan.get('segments')
    if not isinstance(segments, list) or not segments: raise ValueError('有内容的任务至少需要一个分段')
    seen, assets, total, previous_kept = set(), [], 0.0, None
    for segment in segments:
        sid = segment.get('id')
        if not isinstance(sid, str) or not sid.strip() or sid in seen: raise ValueError('分段编号为空或重复')
        seen.add(sid)
        length = number(segment.get('generation_duration_sec'), sid+' 生成时长', True)
        if length not in allowed: raise ValueError(sid+' 生成时长不在接口允许值中')
        start = number(segment.get('use_start_sec'), sid+' 裁切开始')
        end = number(segment.get('use_end_sec'), sid+' 裁切结束', True)
        if not start < end <= length: raise ValueError(sid+' 裁切区间超出生成时长或为空')
        overlap = number(segment.get('transition_overlap_sec', 0), sid+' 转场重叠')
        kept = end-start
        if previous_kept is None and overlap: raise ValueError('第一段不能有前置转场重叠')
        if overlap >= kept or (previous_kept is not None and overlap >= previous_kept):
            raise ValueError(sid+' 转场重叠吞掉了完整片段')
        total += kept-overlap
        previous_kept = kept
        for field in ('prompt', 'image'):
            value = segment.get(field)
            if not isinstance(value, str) or not value.strip(): raise ValueError(f'{sid} 缺少 {field}')
        for field in ('prompt', 'image', 'reference_video', 'dialogue_audio'):
            if not segment.get(field): continue
            path = (base/segment[field]).resolve()
            if not path.is_file() or path.stat().st_size == 0: raise ValueError(f'{sid} {field} 文件缺失或为空')
            if field == 'prompt' and not path.read_text(encoding='utf-8-sig').strip(): raise ValueError(sid+' 提示词为空')
            actual = digest(path)
            expected = segment.get(field+'_sha256')
            if expected and actual != expected: raise ValueError(f'{sid} {field} 版本已改变')
            assets.append({'segment':sid,'role':field,'path':str(path),'sha256':actual,'bytes':path.stat().st_size})
    if not math.isclose(total, target, rel_tol=0, abs_tol=0.001):
        raise ValueError(f'成片计划为 {total:g} 秒，与目标 {target:g} 秒不符')
    return {'valid': True, 'segments': len(segments), 'planned_duration_sec': total,
            'generated_duration_sec':sum(s['generation_duration_sec'] for s in segments),
            'assets':assets, 'scope':'结构、时长与文件版本；未检查实际画面或音轨',
            'generation_authorized':False}

def init_project(args):
    target=number(args.duration,'目标时长',True)
    directory=Path(args.project_dir)
    if directory.exists() and any(directory.iterdir()): raise ValueError('目标目录非空，拒绝覆盖')
    directory.mkdir(parents=True,exist_ok=True)
    for name in ('sources','facts','concepts','dialogue','storyboard','assets','generation','qa','delivery'):
        (directory/name).mkdir(exist_ok=True)
    plan={'schema_version':'1.0','project_id':directory.name,'route':args.route,
          'market':args.market,'language':args.language,'target_duration_sec':target,'image_backend':'local',
          'video_profile':{'backend':'h3-api','provider':None,'model':None,'resolution':None,
                           'allowed_durations_sec':[],'evidence':None,'verified_at':None},
          'segments':[],'unresolved':['补充商品事实和素材','选案和分镜','核实当前 H3 接口参数','本批费用与上传批准']}
    write_new(directory/'project.json',plan)
    return {'created':str(directory.resolve()),'ready_for_generation':False}

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def doctor(url):
    parsed=urlsplit(url)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1') or not parsed.port:
        raise ValueError('只允许本机 http 地址与明确端口')
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/'):
        raise ValueError('本机地址不可带凭据、路径或查询参数')
    with build_opener(ProxyHandler({}),NoRedirect()).open(url.rstrip('/')+'/queue',timeout=5) as response:
        queue=json.load(response)
    if not isinstance(queue.get('queue_running'),list) or not isinstance(queue.get('queue_pending'),list):
        raise ValueError('返回内容不是预期的 ComfyUI 队列')
    return {'available':True,'running':len(queue['queue_running']),'pending':len(queue['queue_pending']),
            'models_verified':False,'generation_started':False}

def main():
    parser=argparse.ArgumentParser(description='整活片场：本地初始化、预检与模型交接')
    subs=parser.add_subparsers(dest='command',required=True)
    p=subs.add_parser('init');p.add_argument('--project-dir',required=True);p.add_argument('--route',choices=ROUTES,required=True)
    p.add_argument('--duration',type=float,required=True);p.add_argument('--market',required=True);p.add_argument('--language',required=True)
    subs.add_parser('modules')
    for name in ('check-plan','prepare-handoff'):
        p=subs.add_parser(name);p.add_argument('--plan',type=Path,required=True)
        if name=='prepare-handoff':p.add_argument('--output',type=Path,required=True)
    p=subs.add_parser('doctor');p.add_argument('--local-url',required=True)
    args=parser.parse_args()
    try:
        if args.command=='init': result=init_project(args)
        elif args.command=='modules':result=read(ROOT/'references'/'modules.json')
        elif args.command=='doctor':result=doctor(args.local_url)
        else:
            plan=read(args.plan);result=validate(plan,args.plan.resolve().parent)
            if args.command=='prepare-handoff':
                result.update({'plan_sha256':digest(args.plan),'video_profile':plan['video_profile'],
                               'segments_plan':plan['segments'],'status':'awaiting_visual_review_and_batch_approval'})
                write_new(args.output,result)
                result={'created':str(args.output.resolve()),'generation_authorized':False,'uploaded':False}
        print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    except (ValueError,KeyError,TypeError,OSError) as exc:
        parser.exit(2,'未通过：'+str(exc)+'\n')

if __name__=='__main__': main()
