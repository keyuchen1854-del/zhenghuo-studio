"""Install only the bundled skill; never overwrite different existing content."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent

def tree_hashes(path):
    return {p.relative_to(path).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}

def install(skill_root):
    source=ROOT/'skills'/'zhenghuo-studio'
    target=Path(skill_root).expanduser()/'zhenghuo-studio'
    if target.exists():
        if tree_hashes(source)==tree_hashes(target): return target,'already_installed'
        raise ValueError('同名技能已有不同内容，拒绝覆盖：'+str(target))
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    if tree_hashes(source)!=tree_hashes(target): raise ValueError('安装后文件校验失败')
    return target,'installed'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='安装整活片场 Codex Skill，不覆盖已有改动')
    parser.add_argument('--skill-root',default=str(Path(os.environ.get('CODEX_HOME',Path.home()/'.codex'))/'skills'))
    args=parser.parse_args()
    try:
        target,status=install(args.skill_root)
        print(status+': '+str(target))
    except (OSError,ValueError) as exc: parser.exit(2,str(exc)+'\n')
