package org.bitflipunix.nuke;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.MotionEvent;
import android.view.View;
import java.util.Random;

/** Original-asset-free first-person Nuketown-inspired training blockout. */
public final class ArenaView extends View {
    private static final int W=24,H=18;
    private final int[][] m=new int[H][W];
    private final Paint p=new Paint(3);
    private final Random rng=new Random(73);
    private final float[] botsX=new float[5],botsY=new float[5];
    private final boolean[] botsLive=new boolean[5];
    private final float[] depth=new float[240];
    private float x=12.0f,y=14.5f,a=-1.57f,vx=0,vy=0;
    private float lastAimX, moveX,moveY;
    private int health=100,score=0,kills=0,frames=0;
    // Deterministic 60 Hz simulation, independent of device rendering refresh rate.
    private static final float FIXED_DT=1f/60f;
    private float accumulated=0;
    private final int[] botAttackCooldown=new int[5];
    private int weaponCooldown=0;
    private boolean victory=false;
    private long last=System.nanoTime();
    private boolean firing=false,dead=false;
    private int leftId=-1,rightId=-1;
    public ArenaView(Context context){super(context);setLayerType(View.LAYER_TYPE_SOFTWARE,null);layout();reset();}
    private void block(int ax,int ay,int bx,int by,int type) {
        for(int j=Math.max(0,ay);j<=Math.min(H-1,by);j++)
            for(int i=Math.max(0,ax);i<=Math.min(W-1,bx);i++)m[j][i]=type;
    }
    private void layout(){
        block(0,0,23,0,1);block(0,17,23,17,1);
        block(0,0,0,17,1);block(23,0,23,17,1);
        // Two opposing house footprints with accessible hallways.
        block(2,2,8,2,2);block(2,2,2,8,2);block(8,2,8,8,2);
        block(2,8,4,8,2);block(6,8,8,8,2);
        block(15,9,21,9,3);block(15,9,15,15,3);block(21,9,21,15,3);
        block(15,15,17,15,3);block(19,15,21,15,3);
        // Central bus and two vehicles.
        block(11,6,12,10,4);block(9,3,10,4,5);block(13,13,14,14,5);
        block(4,11,6,12,6);block(17,4,19,5,6);
        // Middle lane, walkable rear yards and door gaps remain open.
    }
    private boolean solid(float xx,float yy,float r){
        int minX=(int)Math.floor(xx-r),maxX=(int)Math.floor(xx+r);
        int minY=(int)Math.floor(yy-r),maxY=(int)Math.floor(yy+r);
        for(int j=minY;j<=maxY;j++)for(int i=minX;i<=maxX;i++){
            if(i<0||j<0||i>=W||j>=H)return true;
            if(m[j][i]!=0){
                float nx=Math.max(i,Math.min(xx,i+1));
                float ny=Math.max(j,Math.min(yy,j+1));
                if((xx-nx)*(xx-nx)+(yy-ny)*(yy-ny)<r*r)return true;
            }
        }
        return false;
    }
    private void reset(){
        x=12;y=14.5f;a=-1.57f;health=100;score=0;kills=0;frames=0;dead=false;victory=false;accumulated=0;weaponCooldown=0;
        java.util.Arrays.fill(botAttackCooldown,0);
        for(int i=0;i<botsLive.length;i++)spawn(i);
    }
    private void spawn(int i){
        for(int j=0;j<100;j++){
            float bx=1+rng.nextInt(22)+.5f,by=1+rng.nextInt(16)+.5f;
            if(!solid(bx,by,.26f)&&Math.hypot(bx-x,by-y)>4){
                botsX[i]=bx;botsY[i]=by;botsLive[i]=true;return;
            }
        }
        botsLive[i]=false;
    }
    private void step(float dt){
        if(dead)return;
        frames++;
        float f=(float)Math.cos(a)*(-moveY)+(float)Math.cos(a+Math.PI/2)*moveX;
        float g=(float)Math.sin(a)*(-moveY)+(float)Math.sin(a+Math.PI/2)*moveX;
        float s=3.3f*dt;
        float xx=x+f*s,yy=y+g*s;
        if(!solid(xx,y,.23f))x=xx;
        if(!solid(x,yy,.23f))y=yy;
        for(int i=0;i<botsLive.length;i++){
            if(!botsLive[i]) {if(frames%160==i*19)spawn(i);continue;}
            float dx=x-botsX[i],dy=y-botsY[i],dist=(float)Math.hypot(dx,dy);
            if(dist>1.0f&&dist<8.5f){
                float speed=0.68f*dt;
                float tx=botsX[i]+dx/dist*speed,ty=botsY[i]+dy/dist*speed;
                if(!solid(tx,botsY[i],.24f))botsX[i]=tx;
                if(!solid(botsX[i],ty,.24f))botsY[i]=ty;
            }
            if(botAttackCooldown[i]>0)botAttackCooldown[i]--;
            if(dist<5.5f&&botAttackCooldown[i]==0&&lineOfSight(botsX[i],botsY[i],x,y)){
                health=Math.max(0,health-4);
                botAttackCooldown[i]=65+i*4;
            }
        }
        if(weaponCooldown>0)weaponCooldown--;
        if(firing&&weaponCooldown==0){
            weaponCooldown=8;
            float hitDist=9.0f;int target=-1;
            float wx=(float)Math.cos(a),wy=(float)Math.sin(a);
            float wallDist=cast(wx,wy);
            for(int i=0;i<botsLive.length;i++)if(botsLive[i]){
                float dx=botsX[i]-x,dy=botsY[i]-y,proj=dx*wx+dy*wy;
                float side=Math.abs(dx*wy-dy*wx);
                if(proj>0&&proj<hitDist&&proj<wallDist&&side<.28f){
                    target=i;hitDist=proj;
                }
            }
            if(target>=0){botsLive[target]=false;score+=100;kills++;if(kills>=30){victory=true;dead=true;}}
        }
        if(health==0)dead=true;
    }
    /** Shared visibility test for AI and projectile targeting; walls block fire. */
    private boolean lineOfSight(float ax,float ay,float bx,float by){
        float dx=bx-ax,dy=by-ay;
        float dist=(float)Math.hypot(dx,dy);
        if(dist<.001f)return true;
        int n=Math.max(1,(int)Math.ceil(dist/.09f));
        for(int k=1;k<n;k++){
            float t=k/(float)n;
            int ix=(int)Math.floor(ax+dx*t),iy=(int)Math.floor(ay+dy*t);
            if(ix<0||iy<0||ix>=W||iy>=H||m[iy][ix]!=0)return false;
        }
        return true;
    }
    private float cast(float dx,float dy){
        float d=0;
        // DDA-like short ray march; solid ray intersection never penetrates occupied cells.
        for(int k=0;k<320;k++){
            d+=.055f;
            float rx=x+dx*d,ry=y+dy*d;
            int ix=(int)Math.floor(rx),iy=(int)Math.floor(ry);
            if(ix<0||iy<0||ix>=W||iy>=H||m[iy][ix]!=0)return d;
        }
        return 17.6f;
    }
    private int wallColor(int kind,float shade){
        int[][] colors={{60,67,66},{114,112,98},{166,188,183},{186,144,111},{205,171,55},{108,142,166},{119,110,91}};
        int[] b=colors[Math.min(colors.length-1,Math.max(0,kind))];
        return Color.rgb((int)(b[0]*shade),(int)(b[1]*shade),(int)(b[2]*shade));
    }
    private void rectangle(Canvas c,int col,float x1,float y1,float x2,float y2){
        p.setColor(col);p.setStyle(Paint.Style.FILL);c.drawRect(x1,y1,x2,y2,p);
    }
    private void label(Canvas c,String str,float xx,float yy,int size){
        p.setColor(Color.WHITE);p.setTextSize(size);p.setStyle(Paint.Style.FILL);c.drawText(str,xx,yy,p);
    }
    @Override protected void onDraw(Canvas canvas){
        super.onDraw(canvas);
        float w=getWidth(),h=getHeight();
        long now=System.nanoTime();
        float dt=Math.min(.05f,(now-last)/1000000000f);last=now;
        accumulated=Math.min(.20f,accumulated+dt);
        int ticks=0;
        while(accumulated>=FIXED_DT&&ticks<8){step(FIXED_DT);accumulated-=FIXED_DT;ticks++;}
        rectangle(canvas,0xff779db7,0,0,w,h*.5f);
        rectangle(canvas,0xff666b61,0,h*.5f,w,h);
        float focal=h*.74f;
        int columns=depth.length;
        float colwidth=w/columns+1;
        for(int col=0;col<columns;col++){
            float camera=(col+0.5f)/(float)columns-.5f;
            float ang=a+(float)Math.atan(camera*1.12f);
            float dx=(float)Math.cos(ang),dy=(float)Math.sin(ang);
            float dist=cast(dx,dy);
            float corrected=dist*(float)Math.cos(ang-a);
            depth[col]=corrected;
            float tall=Math.min(h*3,focal/Math.max(.08f,corrected));
            float rx=x+dx*dist-.001f*dx,ry=y+dy*dist-.001f*dy;
            int ix=Math.max(0,Math.min(W-1,(int)rx));
            int iy=Math.max(0,Math.min(H-1,(int)ry));
            int kind=m[iy][ix];
            float shade=Math.max(.28f,1f-corrected/23f);
            rectangle(canvas,wallColor(kind,shade),col*colwidth,(h-tall)/2,(col+1)*colwidth,(h+tall)/2);
        }
        // Draw sprites from far to near with depth-buffer occlusion.
        boolean[] drawn=new boolean[botsLive.length];
        for(int count=0;count<botsLive.length;count++){
            int nearest=-1;float best=-1;
            for(int i=0;i<botsLive.length;i++)if(botsLive[i]&&!drawn[i]){
                float d=(botsX[i]-x)*(botsX[i]-x)+(botsY[i]-y)*(botsY[i]-y);
                if(d>best){best=d;nearest=i;}
            }
            if(nearest<0)break;
            drawn[nearest]=true;
            float dx=botsX[nearest]-x,dy=botsY[nearest]-y;
            float forward=dx*(float)Math.cos(a)+dy*(float)Math.sin(a);
            float side=-dx*(float)Math.sin(a)+dy*(float)Math.cos(a);
            if(forward<=.25f)continue;
            float screenX=w*(.5f+side/(forward*1.12f));
            float tall=Math.min(h*2,focal/forward*.85f);
            int col=(int)(screenX/w*columns);
            if(col<0||col>=columns||depth[col]<forward-.3f)continue;
            p.setColor(0xffd5493d);p.setStyle(Paint.Style.FILL);
            canvas.drawOval(screenX-tall*.17f,h*.5f-tall*.46f,screenX+tall*.17f,h*.5f+tall*.45f,p);
            p.setColor(0xfff2ba8b);
            canvas.drawCircle(screenX,h*.5f-tall*.37f,tall*.13f,p);
        }
        float cx=w/2,cy=h/2;
        rectangle(canvas,Color.WHITE,cx-12,cy-1,cx-4,cy+1);
        rectangle(canvas,Color.WHITE,cx+4,cy-1,cx+12,cy+1);
        rectangle(canvas,Color.WHITE,cx-1,cy-12,cx+1,cy-4);
        rectangle(canvas,Color.WHITE,cx-1,cy+4,cx+1,cy+12);
        rectangle(canvas,0xbb101820,0,0,w,50);
        label(canvas,"NUKE-ARM64  |  NUKETOWN-INSPIRED BLOCKOUT  |  HP "+health+"  KILLS "+kills+"/30  SCORE "+score,16,33,Math.max(13,(int)(h*.036f)));
        rectangle(canvas,0x7766bfff,18,h-152,180,h-18);
        rectangle(canvas,0x77e86f47,w-195,h-152,w-20,h-18);
        label(canvas,"MOVE",46,h-75,25);
        label(canvas,"FIRE",w-148,h-75,25);
        label(canvas,"DRAG RIGHT SIDE TO LOOK",w*.38f,h-30,17);
        if(dead){
            rectangle(canvas,0xee10191e,w*.20f,h*.29f,w*.8f,h*.67f);
            label(canvas,(victory?"VICTORY - 30 KILLS":"MATCH OVER")+"   SCORE "+score,w*.28f,h*.44f,30);
            label(canvas,"TAP TO RESTART",w*.35f,h*.55f,25);
        }
        postInvalidateDelayed(16);
    }
    @Override public boolean onTouchEvent(MotionEvent event){
        int action=event.getActionMasked(), index=event.getActionIndex();
        if(dead&&action==MotionEvent.ACTION_DOWN){reset();return true;}
        if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
            int id=event.getPointerId(index);float tx=event.getX(index);
            if(tx<getWidth()*.42f&&leftId<0)leftId=id;
            else if(rightId<0){rightId=id;lastAimX=tx;firing=true;}
        }
        if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_POINTER_UP||action==MotionEvent.ACTION_CANCEL){
            int id=event.getPointerId(index);
            if(id==leftId){leftId=-1;moveX=moveY=0;}
            if(id==rightId){rightId=-1;firing=false;}
        }
        for(int i=0;i<event.getPointerCount();i++){
            int id=event.getPointerId(i);
            if(id==leftId) {
                float xx=event.getX(i)/getWidth(),yy=event.getY(i)/getHeight();
                moveX=Math.max(-1f,Math.min(1f,(xx-.13f)*5));
                moveY=Math.max(-1f,Math.min(1f,(yy-.82f)*5));
            }
            if(id==rightId){
                float xx=event.getX(i);
                if(action==MotionEvent.ACTION_MOVE){a+=(xx-lastAimX)/Math.max(1,getWidth())*3.5f;}
                lastAimX=xx;
            }
        }
        return true;
    }
}
