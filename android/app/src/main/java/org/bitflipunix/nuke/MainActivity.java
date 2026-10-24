package org.bitflipunix.nuke;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Handler;
import android.os.Looper;
import android.widget.FrameLayout;
import android.widget.ProgressBar;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;

/** Never bundles proprietary COD assets. Imports an NMAP made from the user's own OBJ export. */
public final class MainActivity extends Activity {
    private static final int REQUEST_MAP=1001,REQUEST_PHYSICS=1002;
    private NmapView mapView;
    private android.webkit.WebView actionWebView;
    // Expose the already-built KisakBlack JNI bootstrap instead of leaving it untested.
    private static native String nativeStatus();
    private static String nativeBootstrapStatus(){
        try{
            System.loadLibrary("nuke_bootstrap");
            return nativeStatus();
        }catch(UnsatisfiedLinkError e){
            return "Native bootstrap unavailable: "+e.getMessage();
        }
    }
    private final Handler ui=new Handler(Looper.getMainLooper());
    private boolean launching=false;
    private boolean showingMenu=false;
    private int mapLoadGeneration=0;
    private TextView status;
    private final File mapFile(){return new File(getFilesDir(),"user_firingrange.nmap");}

    // Validate a physics import before it can replace the active configuration.
    private static void validatePhysicsDocument(File file) throws Exception {
        org.json.JSONObject root=new org.json.JSONObject(
            new String(java.nio.file.Files.readAllBytes(file.toPath()),
                       java.nio.charset.StandardCharsets.UTF_8));
        if(!"NUKE_PHYSICS_AABB".equals(root.optString("format"))||root.optInt("version")!=1)
            throw new IllegalArgumentException("Expected NUKE_PHYSICS_AABB v1 JSON");
        org.json.JSONObject p=root.getJSONObject("player");
        double radius=p.getDouble("radius"),height=p.getDouble("height");
        double eye=p.getDouble("eye_height"),gravity=p.getDouble("gravity");
        double jump=p.getDouble("jump_speed"),walk=p.getDouble("walk_speed");
        if(!Double.isFinite(radius)||!Double.isFinite(height)||!Double.isFinite(eye)
            ||!Double.isFinite(gravity)||!Double.isFinite(jump)||!Double.isFinite(walk)
            ||radius<=0||height<=eye||eye<=0||walk<=0||gravity>=0||jump<0)
            throw new IllegalArgumentException("Invalid player physics parameters");
        validatePhysicsBoxes(root.getJSONArray("solid_colliders"));
        validatePhysicsBoxes(root.getJSONArray("ground_surfaces"));
    }
    private static void validatePhysicsBoxes(org.json.JSONArray boxes) throws Exception {
        if(boxes.length()>50000)throw new IllegalArgumentException("Too many colliders");
        for(int i=0;i<boxes.length();i++){
            org.json.JSONObject box=boxes.getJSONObject(i);
            org.json.JSONArray lo=box.getJSONArray("min"),hi=box.getJSONArray("max");
            if(lo.length()!=3||hi.length()!=3)
                throw new IllegalArgumentException("Physics collider bounds must have three axes");
            for(int axis=0;axis<3;axis++){
                double min=lo.getDouble(axis),max=hi.getDouble(axis);
                if(!Double.isFinite(min)||!Double.isFinite(max)||min>max)
                    throw new IllegalArgumentException("Invalid physics collider bounds");
            }
        }
    }
    @Override public void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE);
        getWindow().getDecorView().setSystemUiVisibility(5894|1024|512);
        menu();
    }
    private Button button(String label,LinearLayout parent){
        Button b=new Button(this);
        b.setText(label);
        parent.addView(b);
        return b;
    }
    private void menu(){
        mapLoadGeneration++;
        showingMenu=true;
        if(mapView!=null){mapView.onPause();mapView=null;}
        LinearLayout root=new LinearLayout(this);
        root.setPadding(28,16,28,12);
        root.setGravity(Gravity.CENTER);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xff111e25);
        TextView title=new TextView(this);
        title.setText("NUKE-ARM64  |  3D MAP FLYTHROUGH");
        title.setTextColor(0xffbceccd);
        title.setTextSize(24);
        root.addView(title);
        status=new TextView(this);
        status.setTextColor(Color.WHITE);
        status.setTextSize(15);
        status.setPadding(0,12,0,12);
        status.setText("Offline 3D flythrough: left touch to move, right touch to look.\nBundled original-asset-free Nuketown-style blockout. You can also import your own NMAP.\n"+nativeBootstrapStatus());
        root.addView(status);
        button("ACTIONRENDERER3D // NUKETOWN FLYTHROUGH",root).setOnClickListener(v->openAction3D());
        button("LEGACY GLES2 // NUKETOWN FLYTHROUGH",root).setOnClickListener(v->openDemoMap());
        button("PLAY OFFLINE FFA // TEST ARENA",root).setOnClickListener(v->loadingScreen());
        button("IMPORT MAP GEOMETRY (.NMAP)",root).setOnClickListener(v->choose(REQUEST_MAP));
        button("IMPORT MAP PHYSICS (.JSON)",root).setOnClickListener(v->choose(REQUEST_PHYSICS));
        Button open=button("EXPLORE FIRING RANGE / IMPORTED MAP (3D)",root);
        open.setEnabled(mapFile().isFile());
        open.setOnClickListener(v->openMap());
        // Detach before destroying: an abandoned WebView otherwise keeps its JS render loop alive.
        android.webkit.WebView oldWeb=actionWebView;
        actionWebView=null;
        setContentView(root);
        if(oldWeb!=null){oldWeb.onPause();oldWeb.destroy();}
    }

    /** In-app loading presentation: no copyrighted art or false asset-loading claims. */
    private void loadingScreen(){
        if(launching)return;
        showingMenu=false;
        launching=true;
        final int generation=++mapLoadGeneration;
        final FrameLayout frame=new FrameLayout(this);
        GradientDrawable background=new GradientDrawable(
            GradientDrawable.Orientation.TL_BR,
            new int[]{0xff101c20,0xff1b2926,0xff080d10});
        frame.setBackground(background);
        LinearLayout panel=new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(42,22,42,24);
        panel.setGravity(Gravity.CENTER_VERTICAL);
        FrameLayout.LayoutParams pp=new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,FrameLayout.LayoutParams.MATCH_PARENT);
        frame.addView(panel,pp);
        TextView eyebrow=new TextView(this);
        eyebrow.setText("BITFLIPUNIX  /  NUKE-ARM64                                      BUILD 0.2  •  WORK IN PROGRESS");
        eyebrow.setTextColor(0xff8fbcaa);
        eyebrow.setTextSize(13);
        eyebrow.setTypeface(Typeface.MONOSPACE,Typeface.BOLD);
        panel.addView(eyebrow);
        TextView heading=new TextView(this);
        heading.setText("FIRING RANGE");
        heading.setTextSize(66);
        heading.setTextColor(0xffe8e6d9);
        heading.setTypeface(Typeface.create("sans-serif-condensed",Typeface.BOLD));
        panel.addView(heading);
        TextView sub=new TextView(this);
        sub.setText("BLACK OPS 1  //  FREE-FOR-ALL");
        sub.setTextColor(0xffffb868);
        sub.setTextSize(21);
        sub.setTypeface(Typeface.MONOSPACE);
        panel.addView(sub);
        TextView divider=new TextView(this);
        divider.setText("──────────────────────────────────────────────────");
        divider.setTextColor(0xff557a6b);
        divider.setTextSize(16);
        panel.addView(divider);
        TextView mission=new TextView(this);
        mission.setText("NEVADA TEST SITE  /  30 KILL LIMIT  /  5 AI OPPONENTS");
        mission.setTextColor(0xffd6e2da);
        mission.setTextSize(16);
        mission.setTypeface(Typeface.MONOSPACE);
        panel.addView(mission);
        TextView notice=new TextView(this);
        notice.setText("PROTOTYPE FFA BLOCKOUT  •  FIRING RANGE MAP MUST BE IMPORTED SEPARATELY");
        notice.setTextColor(0xffa8b5ad);
        notice.setTextSize(12);
        notice.setPadding(0,16,0,22);
        panel.addView(notice);
        ProgressBar bar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);
        bar.setMax(100);
        bar.setProgress(0);
        panel.addView(bar,new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,12));
        TextView stage=new TextView(this);
        stage.setText("INITIALIZING MATCH  //  0%");
        stage.setTextColor(0xff9dc9b2);
        stage.setTextSize(14);
        stage.setTypeface(Typeface.MONOSPACE);
        stage.setPadding(0,12,0,0);
        panel.addView(stage);
        setContentView(frame);
        final String[] labels={"INITIALIZING MATCH","PREPARING ARENA","SPAWNING AI OPPONENTS","DEPLOYING"};
        for(int i=1;i<=20;i++){
            final int progress=i*5;
            ui.postDelayed(()->{
                if(!launching||generation!=mapLoadGeneration||isFinishing())return;
                bar.setProgress(progress);
                stage.setText(labels[Math.min(labels.length-1,(progress-1)/25)]
                    +"  //  "+progress+"%");
                if(progress==100){
                    launching=false;
                    setContentView(new ArenaView(this));
                }
            },i*105L);
        }
    }
    private void choose(int request){
        Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.setType("*/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(intent,request);
    }
    @Override protected void onActivityResult(int request,int result,Intent intent){
        super.onActivityResult(request,result,intent);
        if((request!=REQUEST_MAP&&request!=REQUEST_PHYSICS)||result!=RESULT_OK||intent==null||intent.getData()==null)return;
        final boolean physics=request==REQUEST_PHYSICS;
        final Uri uri=intent.getData();
        final int generation=++mapLoadGeneration;
        status.setText("Importing map...");
        new Thread(()->{
            File tmp=null;
            try{
                // Unique staging files prevent overlapping imports from corrupting each other.
                tmp=File.createTempFile(physics?"import-physics-":"import-nmap-", ".tmp", getCacheDir());
                try(InputStream in=getContentResolver().openInputStream(uri);
                    FileOutputStream out=new FileOutputStream(tmp)){
                    if(in==null)throw new IllegalArgumentException("Could not open the selected document");
                    byte[] buf=new byte[32768];
                    long size=0;int n;
                    while((n=in.read(buf))!=-1){
                        size+=n;
                        if(size>(physics?1024L*1024:80L*1024*1024))throw new IllegalArgumentException("Import too large");
                        out.write(buf,0,n);
                    }
                    if(size<10)throw new IllegalArgumentException("Selected file is too small");
                    out.getFD().sync();
                }
                // Validate the complete schema after the staged file is closed and synced.
                if(physics)validatePhysicsDocument(tmp);
                final File completed=tmp;
                // Promote only on the UI thread after checking that this import is still current.
                runOnUiThread(()->{
                    if(generation!=mapLoadGeneration||isFinishing()){completed.delete();return;}
                    try{
                        java.nio.file.Files.move(completed.toPath(),
                            physics?new File(getFilesDir(),"arena.physics.json").toPath():mapFile().toPath(),
                            java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                        if(mapFile().isFile())openMap();else menu();
                    }catch(Exception e){
                        completed.delete();
                        if(generation==mapLoadGeneration&&!isFinishing())
                            status.setText("Import failed: "+e.getMessage());
                    }
                });
            }catch(Exception e){
                if(tmp!=null)tmp.delete();
                runOnUiThread(()->{
                    if(generation==mapLoadGeneration&&!isFinishing())
                        status.setText("Import failed: "+e.getMessage());
                });
            }
        }).start();
    }
    private void openAction3D(){
        showingMenu=false;
        mapLoadGeneration++;
        android.webkit.WebView web=new android.webkit.WebView(this);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setAllowFileAccess(true);
        web.setBackgroundColor(0xff101b20);
        web.loadUrl("file:///android_asset/action3d/index.html");
        actionWebView=web;
        setContentView(web);
    }
    private void openDemoMap(){
        showingMenu=false;
        final int generation=++mapLoadGeneration;
        status.setText("Generating standalone 3D map...");
        new Thread(()->{
            try{
                File demo=DemoMap.create(new File(getCacheDir(),"demo_nuketown.nmap"));
                NmapView view=new NmapView(this,demo);
                runOnUiThread(()->{
                    if(generation!=mapLoadGeneration||isFinishing()){view.onPause();return;}
                    mapView=view;setContentView(view);
                });
            }catch(Exception e){runOnUiThread(()->{if(generation==mapLoadGeneration&&!isFinishing())status.setText("Demo map failed: "+e.getMessage());});}
        }).start();
    }
    private void openMap(){
        showingMenu=false;
        final int generation=++mapLoadGeneration;
        status.setText("Loading 3D mesh...");
        new Thread(()->{
            try{
                NmapView view=new NmapView(this,mapFile());
                runOnUiThread(()->{
                    if(generation!=mapLoadGeneration||isFinishing()){view.onPause();return;}
                    mapView=view;setContentView(view);
                });
            }catch(Exception e){
                runOnUiThread(()->{if(generation==mapLoadGeneration&&!isFinishing())status.setText("Map load failed: "+e.getMessage());});
            }
        }).start();
    }
    @Override protected void onPause(){
        if(mapView!=null)mapView.onPause();
        if(actionWebView!=null)actionWebView.onPause();
        super.onPause();
    }
    @Override protected void onResume(){
        super.onResume();
        if(mapView!=null)mapView.onResume();
        if(actionWebView!=null)actionWebView.onResume();
    }
    @Override public void onBackPressed(){
        launching=false;
        if(showingMenu){super.onBackPressed();return;}
        menu();
    }
}
