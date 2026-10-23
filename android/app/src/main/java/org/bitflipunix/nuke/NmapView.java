package org.bitflipunix.nuke;

import android.content.Context;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.Matrix;
import android.view.MotionEvent;
import java.io.File;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.nio.file.Files;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;

/**
 * Standalone untextured NMAP world-geometry preview (Z-up OBJ coordinate system).
 * This is a map viewer, NOT a COD engine or validated gameplay collision solver.
 */
public final class NmapView extends GLSurfaceView implements GLSurfaceView.Renderer {
    private static final int MAX_BYTES=80*1024*1024;
    private static final int MAX_RENDER_TRIANGLES=180000;
    private final FloatBuffer mesh;
    private final int vertexCount;
    private final float[] bounds=new float[6];
    private final float[] projection=new float[16],view=new float[16],mvp=new float[16];
    private final float extent;
    private volatile float yaw=0.5f,pitch=-0.2f,forward=0,strafe=0;
    private float cameraX,cameraY,cameraZ;
    private int program,positionLoc,normalLoc,mvpLoc;
    private final ArrayList<float[]> solids=new ArrayList<>(),floors=new ArrayList<>();
    private float radius=.35f,eyeHeight=1.6f,playerHeight=1.75f,gravity=-18f,jumpSpeed=6f,walkSpeed=5f;
    private float feetZ,verticalSpeed;
    private boolean grounded=false,physicsEnabled=false;
    private volatile boolean jumpRequested=false;
    private long last=System.nanoTime();
    private int movePointer=-1,lookPointer=-1;
    private float moveStartX,moveStartY,lastLookX,lastLookY;

    public NmapView(Context ctx,File map) throws IOException {
        super(ctx);
        setEGLContextClientVersion(2);
        final byte[] bytes=Files.readAllBytes(map.toPath());
        if(bytes.length<40||bytes.length>MAX_BYTES)throw new IOException("Map file must be between 40 bytes and 80 MiB");
        ByteBuffer data=ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
        byte[] magic=new byte[4];data.get(magic);
        if(magic[0]!='N'||magic[1]!='M'||magic[2]!='A'||magic[3]!='P')
            throw new IOException("Invalid NMAP header; convert your exported OBJ first");
        int version=data.getInt(),nv=data.getInt(),nt=data.getInt();
        if(version!=1||nv<3||nv>2000000||nt<1||nt>4000000)
            throw new IOException("Invalid NMAP version or mesh counts");
        long expected=40L+12L*nv+12L*nt;
        if(expected!=bytes.length)throw new IOException("Truncated or unexpected NMAP file length");
        for(int i=0;i<6;i++)bounds[i]=data.getFloat();
        float[] pts=new float[nv*3];
        for(int i=0;i<pts.length;i++)pts[i]=data.getFloat();
        int stride=Math.max(1,(nt+MAX_RENDER_TRIANGLES-1)/MAX_RENDER_TRIANGLES);
        int included=(nt+stride-1)/stride;
        ByteBuffer raw=ByteBuffer.allocateDirect(included*3*6*4).order(ByteOrder.nativeOrder());
        FloatBuffer out=raw.asFloatBuffer();
        int count=0;
        for(int t=0;t<nt;t++){
            int ia=data.getInt(),ib=data.getInt(),ic=data.getInt();
            if(ia<0||ib<0||ic<0||ia>=nv||ib>=nv||ic>=nv)throw new IOException("NMAP index out of bounds");
            if(t%stride!=0)continue;
            float ax=pts[ia*3],ay=pts[ia*3+1],az=pts[ia*3+2];
            float bx=pts[ib*3],by=pts[ib*3+1],bz=pts[ib*3+2];
            float cx=pts[ic*3],cy=pts[ic*3+1],cz=pts[ic*3+2];
            float ux=bx-ax,uy=by-ay,uz=bz-az,vx=cx-ax,vy=cy-ay,vz=cz-az;
            float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
            float d=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(d<1.0e-12f||!Float.isFinite(d))continue;
            nx/=d;ny/=d;nz/=d;
            out.put(ax).put(ay).put(az).put(nx).put(ny).put(nz);
            out.put(bx).put(by).put(bz).put(nx).put(ny).put(nz);
            out.put(cx).put(cy).put(cz).put(nx).put(ny).put(nz);
            count+=3;
        }
        out.flip();
        mesh=out;vertexCount=count;
        extent=Math.max(1f,Math.max(bounds[3]-bounds[0],Math.max(bounds[4]-bounds[1],bounds[5]-bounds[2])));
        cameraX=(bounds[0]+bounds[3])*0.5f-extent*.55f;
        cameraY=(bounds[1]+bounds[4])*0.5f-extent*.55f;
        cameraZ=(bounds[2]+bounds[5])*0.5f+extent*.23f;
        loadPhysics(new File(map.getParentFile(),"arena.physics.json"));
        setRenderer(this);
        setRenderMode(RENDERMODE_CONTINUOUSLY);
    }


    private static float[] box(JSONObject o) throws Exception {
        JSONArray lo=o.getJSONArray("min"),hi=o.getJSONArray("max");
        float[] b=new float[6];
        for(int i=0;i<3;i++){b[i]=(float)lo.getDouble(i);b[i+3]=(float)hi.getDouble(i);
            if(!Float.isFinite(b[i])||!Float.isFinite(b[i+3])||b[i]>b[i+3])
                throw new IOException("Invalid physics collider");}
        return b;
    }
    private void loadPhysics(File file) throws IOException {
        if(!file.isFile())return; // Legacy NMAP remains a free-flight viewer.
        try{
            byte[] raw=Files.readAllBytes(file.toPath());
            if(raw.length>1024*1024)throw new IOException("Physics JSON exceeds 1 MiB");
            JSONObject root=new JSONObject(new String(raw,java.nio.charset.StandardCharsets.UTF_8));
            if(!"NUKE_PHYSICS_AABB".equals(root.getString("format"))||root.getInt("version")!=1)
                throw new IOException("Unsupported physics format");
            JSONObject player=root.getJSONObject("player");
            radius=(float)player.getDouble("radius");
            playerHeight=(float)player.getDouble("height");
            eyeHeight=(float)player.getDouble("eye_height");
            gravity=(float)player.getDouble("gravity");
            jumpSpeed=(float)player.getDouble("jump_speed");
            walkSpeed=(float)player.getDouble("walk_speed");
            if(!Float.isFinite(radius)||!Float.isFinite(playerHeight)||!Float.isFinite(eyeHeight)
                ||!Float.isFinite(gravity)||!Float.isFinite(jumpSpeed)||!Float.isFinite(walkSpeed)
                ||radius<=0||playerHeight<=eyeHeight||eyeHeight<=0||walkSpeed<=0)
                throw new IOException("Invalid player physics parameters");
            JSONArray boxes=root.getJSONArray("solid_colliders"),grounds=root.getJSONArray("ground_surfaces");
            if(boxes.length()>50000||grounds.length()>50000)throw new IOException("Too many colliders");
            for(int i=0;i<boxes.length();i++)solids.add(box(boxes.getJSONObject(i)));
            for(int i=0;i<grounds.length();i++)floors.add(box(grounds.getJSONObject(i)));
            // Start near map centre and settle on highest floor below eye level.
            cameraX=(bounds[0]+bounds[3])*.5f;
            cameraY=(bounds[1]+bounds[4])*.5f;
            feetZ=bounds[2]+.2f;
            for(float[] b:floors)if(cameraX>=b[0]&&cameraX<=b[3]&&cameraY>=b[1]&&cameraY<=b[4])
                feetZ=Math.max(feetZ,b[5]);
            cameraZ=feetZ+eyeHeight;
            physicsEnabled=true;
        }catch(IOException e){throw e;}catch(Exception e){throw new IOException("Physics JSON: "+e.getMessage(),e);}
    }
    private boolean blocked(float px,float py,float bottom){
        for(float[] b:solids){
            if(bottom+playerHeight<=b[2]+.001f||bottom>=b[5]-.001f)continue;
            float nx=Math.max(b[0],Math.min(px,b[3])),ny=Math.max(b[1],Math.min(py,b[4]));
            float dx=px-nx,dy=py-ny;
            if(dx*dx+dy*dy<radius*radius)return true;
        }
        return false;
    }
    private float floorAt(float px,float py,float bottom){
        float top=Float.NEGATIVE_INFINITY;
        for(float[] b:floors)if(px>=b[0]-radius*.5f&&px<=b[3]+radius*.5f
            &&py>=b[1]-radius*.5f&&py<=b[4]+radius*.5f
            &&b[5]<=bottom+.35f&&b[5]>top)top=b[5];
        return top;
    }
    private void physicsStep(float dt){
        if(jumpRequested){jumpRequested=false;if(grounded){verticalSpeed=jumpSpeed;grounded=false;}}
        float dx=((float)Math.cos(yaw)*forward-(float)Math.sin(yaw)*strafe)*walkSpeed*dt;
        float dy=((float)Math.sin(yaw)*forward+(float)Math.cos(yaw)*strafe)*walkSpeed*dt;
        int steps=Math.max(1,(int)Math.ceil(Math.max(Math.abs(dx),Math.abs(dy))/.12f));
        for(int i=0;i<steps;i++){
            float nx=cameraX+dx/steps,ny=cameraY+dy/steps;
            if(!blocked(nx,cameraY,feetZ))cameraX=nx;
            if(!blocked(cameraX,ny,feetZ))cameraY=ny;
        }
        verticalSpeed+=gravity*dt;
        float next=feetZ+verticalSpeed*dt;
        float floor=floorAt(cameraX,cameraY,Math.max(feetZ,next));
        if(verticalSpeed<=0&&floor!=Float.NEGATIVE_INFINITY&&next<=floor){
            next=floor;verticalSpeed=0;grounded=true;
        }else grounded=false;
        feetZ=next;cameraZ=feetZ+eyeHeight;
    }
    private static int shader(int kind,String source){
        int id=GLES20.glCreateShader(kind);
        GLES20.glShaderSource(id,source);
        GLES20.glCompileShader(id);
        int[] ok=new int[1];GLES20.glGetShaderiv(id,GLES20.GL_COMPILE_STATUS,ok,0);
        if(ok[0]==0)throw new IllegalStateException("Shader compile: "+GLES20.glGetShaderInfoLog(id));
        return id;
    }
    @Override public void onSurfaceCreated(javax.microedition.khronos.opengles.GL10 gl,
                                           javax.microedition.khronos.egl.EGLConfig config){
        String vert="attribute vec3 aPos;attribute vec3 aNorm;uniform mat4 uMvp;"
            +"varying float vShade;void main(){gl_Position=uMvp*vec4(aPos,1.0);"
            +"vShade=0.35+0.5*abs(aNorm.z)+0.15*abs(aNorm.y);}";
        String frag="precision mediump float;varying float vShade;"
            +"void main(){gl_FragColor=vec4(vec3(0.77,0.75,0.69)*vShade,1.0);}";
        program=GLES20.glCreateProgram();
        GLES20.glAttachShader(program,shader(GLES20.GL_VERTEX_SHADER,vert));
        GLES20.glAttachShader(program,shader(GLES20.GL_FRAGMENT_SHADER,frag));
        GLES20.glLinkProgram(program);
        int[] ok=new int[1];GLES20.glGetProgramiv(program,GLES20.GL_LINK_STATUS,ok,0);
        if(ok[0]==0)throw new IllegalStateException("Shader link: "+GLES20.glGetProgramInfoLog(program));
        positionLoc=GLES20.glGetAttribLocation(program,"aPos");
        normalLoc=GLES20.glGetAttribLocation(program,"aNorm");
        mvpLoc=GLES20.glGetUniformLocation(program,"uMvp");
        GLES20.glEnable(GLES20.GL_DEPTH_TEST);
        GLES20.glDisable(GLES20.GL_CULL_FACE);
        GLES20.glClearColor(.43f,.55f,.67f,1f);
    }
    @Override public void onSurfaceChanged(javax.microedition.khronos.opengles.GL10 gl,int width,int height){
        GLES20.glViewport(0,0,width,height);
        Matrix.perspectiveM(projection,0,72,(float)width/Math.max(1,height),Math.max(.005f,extent*.0005f),extent*8f);
    }
    @Override public void onDrawFrame(javax.microedition.khronos.opengles.GL10 gl){
        long now=System.nanoTime();float dt=Math.min(.055f,Math.max(0,(now-last)/1e9f));last=now;
        if(physicsEnabled)physicsStep(dt);
        else {
        float speed=Math.max(1f,extent*.15f);
        cameraX+=((float)Math.cos(yaw)*forward-(float)Math.sin(yaw)*strafe)*speed*dt;
        cameraY+=((float)Math.sin(yaw)*forward+(float)Math.cos(yaw)*strafe)*speed*dt;
        }
        float cp=(float)Math.cos(pitch);
        Matrix.setLookAtM(view,0,cameraX,cameraY,cameraZ,
            cameraX+(float)Math.cos(yaw)*cp,
            cameraY+(float)Math.sin(yaw)*cp,
            cameraZ+(float)Math.sin(pitch),0,0,1);
        Matrix.multiplyMM(mvp,0,projection,0,view,0);
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT|GLES20.GL_DEPTH_BUFFER_BIT);
        GLES20.glUseProgram(program);
        GLES20.glUniformMatrix4fv(mvpLoc,1,false,mvp,0);
        GLES20.glEnableVertexAttribArray(positionLoc);
        GLES20.glEnableVertexAttribArray(normalLoc);
        mesh.position(0);
        GLES20.glVertexAttribPointer(positionLoc,3,GLES20.GL_FLOAT,false,24,mesh);
        mesh.position(3);
        GLES20.glVertexAttribPointer(normalLoc,3,GLES20.GL_FLOAT,false,24,mesh);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLES,0,vertexCount);
        GLES20.glDisableVertexAttribArray(positionLoc);
        GLES20.glDisableVertexAttribArray(normalLoc);
    }
    @Override public boolean onTouchEvent(MotionEvent ev){
        int action=ev.getActionMasked(),idx=ev.getActionIndex();
        // Android cancels the entire gesture, not just the action-index pointer.
        if(action==MotionEvent.ACTION_CANCEL){
            movePointer=lookPointer=-1;
            forward=strafe=0;
            jumpRequested=false;
            return true;
        }
        if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
            int id=ev.getPointerId(idx);
            if(physicsEnabled&&ev.getX(idx)>getWidth()*.80f&&ev.getY(idx)<getHeight()*.32f){jumpRequested=true;return true;}
            if(ev.getX(idx)<getWidth()*.45f&&movePointer<0){
                movePointer=id;moveStartX=ev.getX(idx);moveStartY=ev.getY(idx);
            }else if(lookPointer<0){
                lookPointer=id;lastLookX=ev.getX(idx);lastLookY=ev.getY(idx);
            }
        }
        if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_POINTER_UP||action==MotionEvent.ACTION_CANCEL){
            int id=ev.getPointerId(idx);
            if(id==movePointer){movePointer=-1;forward=strafe=0;}
            if(id==lookPointer)lookPointer=-1;
        }
        if(action==MotionEvent.ACTION_MOVE){
            for(int i=0;i<ev.getPointerCount();i++){
                int id=ev.getPointerId(i);
                if(id==movePointer){
                    strafe=Math.max(-1,Math.min(1,(ev.getX(i)-moveStartX)/110f));
                    forward=Math.max(-1,Math.min(1,(moveStartY-ev.getY(i))/110f));
                } else if(id==lookPointer){
                    yaw+=(ev.getX(i)-lastLookX)/Math.max(1,getWidth())*4f;
                    pitch=Math.max(-1.4f,Math.min(1.4f,pitch-(ev.getY(i)-lastLookY)/Math.max(1,getHeight())*2f));
                    lastLookX=ev.getX(i);lastLookY=ev.getY(i);
                }
            }
        }
        return true;
    }
}
