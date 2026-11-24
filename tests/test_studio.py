import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
studio=load('studio',ROOT/'skills/zhenghuo-studio/scripts/studio.py')
installer=load('installer',ROOT/'install.py')

class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        (self.base/'prompt.txt').write_text('fixture: turn toward camera',encoding='utf-8')
        # This is deliberately not an actual image: validation is structural, not visual.
        (self.base/'image.bin').write_bytes(b'fixture-image-content')
        self.plan={'schema_version':'1.0','project_id':'test','route':'original','market':'fixture-market','language':'en',
                   'target_duration_sec':10,'image_backend':'local',
                   'video_profile':{'backend':'h3-api','provider':'fixture','model':'fixture','resolution':'fixture',
                                    'allowed_durations_sec':[5,15],'evidence':'test fixture, not service capability','verified_at':'fixture'},
                   'segments':[self.segment('A'),self.segment('B')]}
    def tearDown(self): self.temp.cleanup()
    def segment(self,sid):
        return {'id':sid,'generation_duration_sec':5,'use_start_sec':0,'use_end_sec':5,'transition_overlap_sec':0,
                'prompt':'prompt.txt','image':'image.bin'}
    def check(self): return studio.validate(self.plan,self.base)
    def test_valid_plan_has_no_generation_authority(self):
        result=self.check();self.assertEqual(result['planned_duration_sec'],10);self.assertFalse(result['generation_authorized'])
    def test_short_video_needs_one_segment(self):
        self.plan['target_duration_sec']=3;self.plan['segments']=[self.segment('A')]
        self.plan['segments'][0]['use_end_sec']=3
        self.assertEqual(self.check()['segments'],1)
        self.plan['segments']=[]
        with self.assertRaises(ValueError):self.check()
    def test_rejects_three_fifteens_as_thirty(self):
        self.plan['target_duration_sec']=30;self.plan['segments']=[self.segment(x) for x in ('A','B','C')]
        for s in self.plan['segments']:s.update(generation_duration_sec=15,use_end_sec=15)
        with self.assertRaises(ValueError):self.check()
    def test_overlap_changes_final_duration(self):
        self.plan['segments'][1]['transition_overlap_sec']=1;self.plan['target_duration_sec']=9
        self.assertEqual(self.check()['planned_duration_sec'],9)
    def test_bad_overlap_and_trim_rejected(self):
        for field,value in [('use_start_sec',6),('use_end_sec',6),('transition_overlap_sec',5)]:
            with self.subTest(field=field):
                old=copy.deepcopy(self.plan);self.plan['segments'][1][field]=value
                with self.assertRaises(ValueError):self.check()
                self.plan=old
    def test_nonfinite_and_boolean_duration_rejected(self):
        for value in [0,-1,float('nan'),float('inf'),True]:
            with self.subTest(value=value):
                self.plan['target_duration_sec']=value
                with self.assertRaises(ValueError):self.check()
    def test_duplicate_and_missing_segments_rejected(self):
        self.plan['segments'][1]['id']='A'
        with self.assertRaises(ValueError):self.check()
    def test_unsupported_backend_and_duration_rejected(self):
        self.plan['segments'][0]['generation_duration_sec']=6
        with self.assertRaises(ValueError):self.check()
        self.plan['segments'][0]['generation_duration_sec']=5;self.plan['image_backend']='cloud'
        with self.assertRaises(ValueError):self.check()
    def test_missing_or_changed_asset_rejected(self):
        self.plan['segments'][0]['image_sha256']=studio.digest(self.base/'image.bin')
        (self.base/'image.bin').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.check()
        (self.base/'image.bin').unlink()
        with self.assertRaises(ValueError):self.check()
    def test_initial_plan_is_unapproved_and_incomplete(self):
        directory=self.base/'new'
        studio.init_project(SimpleNamespace(project_dir=str(directory),duration=30,route='original',market='test',language='en'))
        with self.assertRaises(ValueError):studio.validate(studio.read(directory/'project.json'),directory)
        with self.assertRaises(ValueError):studio.init_project(SimpleNamespace(project_dir=str(directory),duration=30,route='original',market='test',language='en'))
    def test_handoff_write_does_not_overwrite(self):
        path=self.base/'handoff.json';result=self.check();studio.write_new(path,result)
        self.assertFalse(json.loads(path.read_text(encoding='utf-8'))['generation_authorized'])
        with self.assertRaises(FileExistsError):studio.write_new(path,result)
    def test_doctor_rejects_remote_or_credentialed_urls(self):
        for url in ('https://example.com:443','http://user:password@127.0.0.1:8198','http://127.0.0.1:8198/api'):
            with self.assertRaises(ValueError):studio.doctor(url)
    def test_installer_preserves_existing_edits(self):
        dest,status=installer.install(self.base/'skills');self.assertEqual(status,'installed')
        self.assertEqual(installer.install(self.base/'skills')[1],'already_installed')
        (dest/'SKILL.md').write_text('local change',encoding='utf-8')
        with self.assertRaises(ValueError):installer.install(self.base/'skills')
        self.assertEqual((dest/'SKILL.md').read_text(encoding='utf-8'),'local change')
    def test_all_thirteen_modules_are_available(self):
        skill=ROOT/'skills/zhenghuo-studio';modules=studio.read(skill/'references/modules.json')
        self.assertEqual(len(modules),13);self.assertEqual(len({x['id'] for x in modules}),13)
        for item in modules:self.assertTrue((skill/item['path']).is_file())

if __name__=='__main__':unittest.main()
