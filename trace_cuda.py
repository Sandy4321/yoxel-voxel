#!/usr/bin/python
import pycuda.driver as cuda
import pycuda.gpuarray as ga
from numpy import *
import struct

from time import clock

from ore.ore import *


def normalize(v):
    vn = sqrt( (v**2).sum() )
    return v / vn


class CudaRenderer:
    def __init__(self, res=(640, 480)):
        opts = ['-DUSE_TEXLOOKUP']

        mod = cuda.SourceModule(file("cpp/trace.cu").read(), keep=True, options=['-I../cpp'] + opts, no_extern_c=True)
        self.InitEyeRays = mod.get_function("InitEyeRays")
        self.InitFishEyeRays = mod.get_function("InitFishEyeRays")
        self.InitShadowRays = mod.get_function("InitShadowRays")
        self.Trace = mod.get_function("Trace")
        self.ShadeShadow = mod.get_function("ShadeShadow")
        self.ShadeSimple = mod.get_function("ShadeSimple")
        self.mod = mod

        self.block = (16, 32, 1)  # 15: 32, 18: 28, 19: 24
        self.grid = ( res[0]/self.block[0], res[1]/self.block[1] )
        self.resx, self.resy = (self.grid[0]*self.block[0], self.grid[1]*self.block[1])

        self.smallblock = (16, 16, 1)
        self.smallgrid = ( res[0]/self.smallblock[0], res[1]/self.smallblock[1] )

        self.d_img = ga.empty( (self.resy, self.resx, 4), uint8 )

        '''
        struct RayData
        {
          float3 dir;
          float t;
          VoxNodeId endNode;
          float endNodeSize;
        };
        '''
        raySize = struct.calcsize("3f f i f")
        self.d_rays = ga.empty( (self.resy, self.resx, raySize), uint8 )
        self.d_shadowRays = ga.empty( (self.resy, self.resx, raySize), uint8 )

        self.setLightPos((0.5, 0.5, 1))
        self.detailCoef = 10.0

    def updateScene(self, scene):
        (self.sceneRoot, nodes, leafs) = scene.GetData()

        self.texrefs = [self.mod.get_texref(name+"_tex") for name in ["nodes", "leafs"]]
        self.texrefs[0].set_address(nodes[0], nodes[1])
        self.texrefs[1].set_address(leafs[0], leafs[1])

        args = [self.sceneRoot, nodes[0], leafs[0]]
        st = struct.pack("iPP", *args)
        tree_glb = self.mod.get_global("tree")
        cuda.memcpy_htod(tree_glb[0], st)

    def setLightPos(self, pos):
        self.lightPos = pos

    def getViewSize(self):
        return (self.resx, self.resy)

    def buildTraceParams(self, eyePos, detail):
        '''
        struct TraceParams
        {
          float3 start;
          
          float detailCoef;
          VoxNodeId startNode;
          float3 startNodePos;
          float  startNodeSize;
          int startNodeLevel;
        };
        '''

        args = []
        (node, pos, size, level) = (self.sceneRoot, (0, 0, 0), 1, 0)
        args.extend(eyePos)
        args.append(2*3.1415/360.0 / detail)
        args.append(node)
        args.extend(pos)
        args.append(size)
        args.append(level)
        return struct.pack("3f f i 3f f i", *args)
   

    def render(self, eyePos, viewDir, first=False):
        vdir = array(viewDir, float32)
        vdir = normalize(vdir)
        vright = normalize( cross(vdir, (0, 0, 1)) )
        vup = normalize( cross(vright, vdir) )

        args = []
        args.extend(eyePos)
        args.extend(vdir)
        args.extend(vright)
        args.extend(vup)
        args.extend(self.lightPos)
        render_params = struct.pack("3f 3f 3f 3f 3f", *args)

        trace_params = self.buildTraceParams(eyePos, self.detailCoef)
        shadowTrace_params = self.buildTraceParams(self.lightPos, self.detailCoef)

        t = clock()
        self.InitEyeRays(render_params, self.d_rays, block=self.smallblock, grid=self.smallgrid, time_kernel=True, texrefs=self.texrefs)
        
        trace1Begin = clock()
        self.Trace(trace_params, self.d_rays, block=self.block, grid=self.grid, time_kernel=True, texrefs=self.texrefs)
        trace1End = clock()

        #self.InitShadowRays(render_params, self.d_rays, self.d_shadowRays, trace_params, block=self.smallblock, grid=self.smallgrid, time_kernel=True, texrefs=self.texrefs)

        trace2Begin = clock()
        #self.Trace(shadowTrace_params, self.d_shadowRays, block=self.block, grid=self.grid, time_kernel=True, texrefs=self.texrefs)
        trace2End = clock()
        
        self.ShadeSimple(render_params, self.d_rays, self.d_shadowRays, self.d_img, block=self.smallblock, grid=self.smallgrid, time_kernel=True, texrefs=self.texrefs)
        gpuTime = clock()-t

        trace1Time = trace1End - trace1Begin
        trace2Time = trace2End - trace2Begin

        stat = "gpu time: %.2f ms\n" % (gpuTime*1000)
        stat += "eye trace time: %.2f ms\n" % (trace1Time*1000)
        stat += "shadow trace time: %.2f ms\n" % (trace2Time*1000)
        stat += "detailCoef: %f\n" % (self.detailCoef)

        return stat

    def getImage(self):
        return self.d_img.get()[...,:3]

if __name__ == '__main__':
    cuda.init()
    assert cuda.Device.count() >= 1
    dev = cuda.Device(0)
    ctx = dev.make_context()

    renderer = CudaRenderer(loadScene("data/hmap.vox"))

    #from render import renderTurn
    #renderTurn(renderer)
