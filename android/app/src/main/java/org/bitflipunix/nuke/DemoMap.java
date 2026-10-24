package org.bitflipunix.nuke;

import java.io.*;
import java.nio.*;
import java.util.*;

/** Original-asset-free Nuketown-style training blockout, generated locally. */
public final class DemoMap {
    private final ArrayList<float[]> vertices=new ArrayList<>();
    private final ArrayList<int[]> triangles=new ArrayList<>();
    private DemoMap(){}
    private int v(float x,float y,float z){vertices.add(new float[]{x,y,z});return vertices.size()-1;}
    private void quad(int a,int b,int c,int d){triangles.add(new int[]{a,b,c});triangles.add(new int[]{a,c,d});}
    private void box(float x,float y,float z,float w,float h,float d){
        int a=v(x,y,z),b=v(x+w,y,z),c=v(x+w,y+h,z),e=v(x,y+h,z);
        int f=v(x,y,z+d),g=v(x+w,y,z+d),i=v(x+w,y+h,z+d),j=v(x,y+h,z+d);
        quad(a,e,c,b);quad(f,g,i,j);quad(a,b,g,f);quad(b,c,i,g);quad(c,e,j,i);quad(e,a,f,j);
    }
    private void scene(){
        box(-16,-13,-.5f,32,26,.5f);
        // Opposing houses with separated walls and walkable entrances.
        box(-13,-10,0,9,.35f,5);box(-13,-10,0,.35f,9,5);
        box(-4.35f,-10,0,.35f,3.5f,5);box(-4.35f,-3.5f,0,.35f,2.5f,5);
        box(-13,-1.35f,0,3,.35f,5);box(-7,-1.35f,0,3,.35f,5);
        box(-13,-10,5,9,9,.3f);
        box(4,1,0,9,.35f,5);box(4,1,0,.35f,9,5);
        box(12.65f,1,0,.35f,9,5);
        box(4,9.65f,0,3,.35f,5);box(10,9.65f,0,3,.35f,5);
        box(4,1,5,9,9,.3f);
        // Centre bus, trucks, garden walls and cover.
        box(-1.6f,-5,0,3.2f,10,3.3f);
        box(-6,4,0,3.3f,2.4f,1.9f);
        box(4,-6,0,3.3f,2.4f,1.9f);
        box(-15,2,0,4,.4f,1.5f);box(11,-3,0,4,.4f,1.5f);
        box(-16,-13,0,32,.4f,2.3f);box(-16,12.6f,0,32,.4f,2.3f);
        box(-16,-13,0,.4f,26,2.3f);box(15.6f,-13,0,.4f,26,2.3f);
    }
    public static File create(File dest) throws IOException{
        DemoMap map=new DemoMap();map.scene();
        int nv=map.vertices.size(),nt=map.triangles.size();
        ByteBuffer buf=ByteBuffer.allocate(40+12*nv+12*nt).order(ByteOrder.LITTLE_ENDIAN);
        buf.put(new byte[]{'N','M','A','P'}).putInt(1).putInt(nv).putInt(nt);
        for(float n:new float[]{-16,-13,-.5f,16,13,5.3f})buf.putFloat(n);
        for(float[] p:map.vertices)for(float n:p)buf.putFloat(n);
        for(int[] t:map.triangles)for(int n:t)buf.putInt(n);
        try(FileOutputStream out=new FileOutputStream(dest)){out.write(buf.array());}
        return dest;
    }
}
