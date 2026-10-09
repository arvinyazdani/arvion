import test from 'node:test';import assert from 'node:assert/strict';import {clamp,phase,frame} from './film-model.mjs';
test('out of range and invalid progress is bounded',()=>{assert.equal(clamp(-3),0);assert.equal(clamp(8),1);assert.equal(clamp(NaN),0);});
test('start is an idea and finish is a connected site',()=>{assert.deepEqual(frame(0),{p:0,blueprint:0,site:0,phone:0,network:0,chapter:0});assert.deepEqual(frame(1),{p:1,blueprint:1,site:1,phone:1,network:1,chapter:4});});
test('continuous frames do not jump at chapter boundaries',()=>{for(const p of [.2,.4,.6,.8])for(const k of ['blueprint','site','phone','network'])assert.ok(Math.abs(frame(p-.0001)[k]-frame(p+.0001)[k])<.01);});
test('scroll back restores exactly the same frame without hidden history',()=>{const previous=frame(.47);frame(.95);assert.deepEqual(frame(.47),previous);});
test('all phases are monotonic, bounded and ordered',()=>{for(let i=0;i<=1000;i++){const f=frame(i/1000);assert.ok(f.blueprint>=f.site&&f.site>=f.phone&&f.phone>=f.network);for(const k of ['blueprint','site','phone','network'])assert.ok(f[k]>=0&&f[k]<=1);}});
test('phase has smooth endpoints',()=>{assert.equal(phase(0,.2,.4),0);assert.equal(phase(1,.2,.4),1);assert.ok(Math.abs(phase(.3,.2,.4)-.5)<1e-12);});
