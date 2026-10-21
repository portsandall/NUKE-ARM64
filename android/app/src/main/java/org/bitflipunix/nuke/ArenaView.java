package org.bitflipunix.nuke;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Color;
import android.graphics.RectF;
import android.view.View;
import android.view.MotionEvent;
import java.util.Random;

/** Playable top-down Nuketown-inspired blockout. No original game assets. */
public final class ArenaView extends View {
    private final Paint p = new Paint(3);
    private final Random random = new Random(7);
    private final float[][] walls = {
        {60,60,310,275}, {690,60,940,275}, // houses
        {60,525,310,740}, {690,525,940,740}, // rear gardens/sheds
        {425,285,565,470}, // bus
        {315,80,405,175}, {600,625,690,720}, // vehicles
        {120,330,205,430},{790,345,885,445}
    };
    private final float[] ex = new float[6], ey = new float[6];
    private final boolean[] alive = new boolean[6];
    private float px=500,py=590, aimx=500, aimy=200;
    private float joyx=0,joyy=0;
    private boolean shoot=false, gameover=false;
    private int score=0,hp=100,ticks=0;
    private long last=System.nanoTime();
    public ArenaView(Context ctx) { super(ctx); setLayerType(View.LAYER_TYPE_SOFTWARE,null); reset(); }
    private void reset() {
        px=500;py=590;hp=100;score=0;ticks=0;gameover=false;
        for(int i=0;i<6;i++) respawn(i);
    }
    private void respawn(int i) {
        for(int tries=0;tries<100;tries++) {
            float x=70+random.nextInt(860), y=70+random.nextInt(650);
            if(!blocked(x,y,18) && Math.hypot(x-px,y-py)>220) {
                ex[i]=x;ey[i]=y;alive[i]=true;return;
            }
        }
        alive[i]=false;
    }
    private boolean blocked(float x,float y,float r) {
        if(x<r||x>1000-r||y<r||y>800-r) return true;
        for(float[] a:walls) if(x+r>a[0]&&x-r<a[2]&&y+r>a[1]&&y-r<a[3]) return true;
        return false;
    }
    private void movePlayer(float dx,float dy) {
        if(!blocked(px+dx,py,14)) px+=dx;
        if(!blocked(px,py+dy,14)) py+=dy;
    }
    private void rect(Canvas c,int col,float a,float b,float d,float e) {
        p.setColor(col);p.setStyle(Paint.Style.FILL);c.drawRect(a,b,d,e,p);
    }
    private void circle(Canvas c,int col,float x,float y,float r) {
        p.setColor(col);p.setStyle(Paint.Style.FILL);c.drawCircle(x,y,r,p);
    }
    private void line(Canvas c,int col,float x,float y,float xx,float yy,float sw){
        p.setColor(col);p.setStrokeWidth(sw);c.drawLine(x,y,xx,yy,p);
    }
    private void text(Canvas c,String s,float x,float y,int size,int col){
        p.setColor(col);p.setTextSize(size);p.setStyle(Paint.Style.FILL);c.drawText(s,x,y,p);
    }
    private void update(float dt) {
        if(gameover) return;
        ticks++;
        float len=(float)Math.hypot(joyx,joyy);
        if(len>0.01f) movePlayer(joyx/Math.max(1,len)*170*dt,joyy/Math.max(1,len)*170*dt);
        for(int i=0;i<6;i++){
            if(!alive[i]){if(ticks%150==i*20)respawn(i);continue;}
            float dx=px-ex[i],dy=py-ey[i],dist=(float)Math.hypot(dx,dy);
            if(dist>75&&dist<500){
                float speed=45*dt;
                float mx=dx/dist*speed,my=dy/dist*speed;
                if(!blocked(ex[i]+mx,ey[i],14))ex[i]+=mx;
                if(!blocked(ex[i],ey[i]+my,14))ey[i]+=my;
            }
            if(dist<45&&ticks%26==i%6)hp-=5;
        }
        if(shoot&&ticks%9==0) {
            float ax=aimx-px,ay=aimy-py,mag=(float)Math.hypot(ax,ay);
            if(mag<1){ax=0;ay=-1;mag=1;}
            ax/=mag;ay/=mag;
            int hit=-1;float best=420;
            for(int i=0;i<6;i++)if(alive[i]){
                float rx=ex[i]-px,ry=ey[i]-py,proj=rx*ax+ry*ay;
                float perp=Math.abs(rx*ay-ry*ax);
                if(proj>0&&proj<best&&perp<23){hit=i;best=proj;}
            }
            if(hit>=0) {alive[hit]=false;score+=100;}
        }
        if(hp<=0)gameover=true;
    }
    @Override protected void onDraw(Canvas raw){
        super.onDraw(raw);
        float sx=getWidth()/1000f,sy=getHeight()/800f;
        Canvas c=raw;c.save();c.scale(sx,sy);
        long now=System.nanoTime();float dt=Math.min(.045f,(now-last)/1000000000f);last=now;update(dt);
        rect(c,Color.rgb(76,105,72),0,0,1000,800);
        rect(c,Color.rgb(90,91,82),310,0,690,800);
        line(c,0xffd8d0ad,500,0,500,800,4);
        for(int i=0;i<walls.length;i++){
            float[] a=walls[i];
            int color=i<4?0xffb0af9e:(i==4?0xffd3b84d:0xff7193ac);
            rect(c,color,a[0],a[1],a[2],a[3]);
            p.setColor(0xff303d3c);p.setStrokeWidth(4);p.setStyle(Paint.Style.STROKE);
            c.drawRect(new RectF(a[0],a[1],a[2],a[3]),p);p.setStyle(Paint.Style.FILL);
        }
        rect(c,0xffa4aba8,35,285,285,300);
        rect(c,0xffa4aba8,715,500,965,515);
        for(int i=0;i<6;i++)if(alive[i]) {circle(c,0xffe85b57,ex[i],ey[i],15);circle(c,0xff5b1818,ex[i],ey[i],5);}
        circle(c,0xff56d7ff,px,py,16);
        float ax=aimx-px,ay=aimy-py,d=(float)Math.hypot(ax,ay);
        if(d>1)line(c,0xfff6f3d4,px,py,px+ax/d*35,py+ay/d*35,5);
        rect(c,0xcc101920,0,0,1000,55);
        text(c,"NUKE-ARM64  |  BLOCKOUT ARENA  |  SCORE "+score+"  |  HP "+Math.max(hp,0),18,37,26,Color.WHITE);
        circle(c,0x8840e0ff,130,655,90);
        text(c,"MOVE",91,665,24,Color.WHITE);
        circle(c,0x88ff704d,860,660,85);
        text(c,"FIRE",828,670,27,Color.WHITE);
        if(gameover) {
            rect(c,0xdd0b1720,140,285,860,500);
            text(c,"MATCH OVER  -  SCORE "+score,260,375,35,Color.WHITE);
            text(c,"TAP TO RESTART",357,425,25,Color.WHITE);
        }
        c.restore();postInvalidateDelayed(16);
    }
    @Override public boolean onTouchEvent(MotionEvent e) {
        int action=e.getActionMasked();
        if(gameover&&action==MotionEvent.ACTION_DOWN){reset();return true;}
        joyx=joyy=0;shoot=false;
        for(int i=0;i<e.getPointerCount();i++){
            if(action==MotionEvent.ACTION_POINTER_UP&&i==e.getActionIndex())continue;
            float x=e.getX(i)*1000f/Math.max(1,getWidth());
            float y=e.getY(i)*800f/Math.max(1,getHeight());
            if(x<440&&y>490) {
                joyx=Math.max(-1,Math.min(1,(x-130)/90));
                joyy=Math.max(-1,Math.min(1,(y-655)/90));
            }else if(x>580&&y>490){
                shoot=true;aimx=px+(x-860);aimy=py+(y-660)-200;
            }else if(action!=MotionEvent.ACTION_UP){aimx=x;aimy=y;}
        }
        invalidate();return true;
    }
}
