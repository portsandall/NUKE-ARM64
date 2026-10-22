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
    private static final int REQUEST_MAP=1001;
    private NmapView mapView;
    private final Handler ui=new Handler(Looper.getMainLooper());
    private boolean launching=false;
    private TextView status;
    private final File mapFile(){return new File(getFilesDir(),"user_nuketown.nmap");}
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
        if(mapView!=null){mapView.onPause();mapView=null;}
        LinearLayout root=new LinearLayout(this);
        root.setPadding(28,16,28,12);
        root.setGravity(Gravity.CENTER);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xff111e25);
        TextView title=new TextView(this);
        title.setText("NUKE-ARM64  |  NUKETOWN STANDALONE");
        title.setTextColor(0xffbceccd);
        title.setTextSize(24);
        root.addView(title);
        status=new TextView(this);
        status.setTextColor(Color.WHITE);
        status.setTextSize(15);
        status.setPadding(0,12,0,12);
        status.setText("Original map geometry is not included. Import a .nmap made from your own Black Ops OBJ export.\nImported mesh preview: touch left to move, right to look. Collision, textures and COD gameplay are not yet implemented.");
        root.addView(status);
        button("DEPLOY // OFFLINE FFA PROTOTYPE",root).setOnClickListener(v->loadingScreen());
        button("IMPORT EXPORTED NUKETOWN .NMAP",root).setOnClickListener(v->choose());
        Button open=button("EXPLORE IMPORTED MAP (3D)",root);
        open.setEnabled(mapFile().isFile());
        open.setOnClickListener(v->openMap());
        setContentView(root);
    }

    /** In-app loading presentation: no copyrighted art or false asset-loading claims. */
    private void loadingScreen(){
        if(launching)return;
        launching=true;
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
        heading.setText("NUKETOWN");
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
        notice.setText("PROTOTYPE ENVIRONMENT  •  ORIGINAL BO1 MAP ASSETS NOT YET INTEGRATED");
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
                if(!launching||isFinishing())return;
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
    private void choose(){
        Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.setType("*/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(intent,REQUEST_MAP);
    }
    @Override protected void onActivityResult(int request,int result,Intent intent){
        super.onActivityResult(request,result,intent);
        if(request!=REQUEST_MAP||result!=RESULT_OK||intent==null||intent.getData()==null)return;
        final Uri uri=intent.getData();
        status.setText("Importing map...");
        new Thread(()->{
            File tmp=new File(getCacheDir(),"import.nmap");
            try(InputStream in=getContentResolver().openInputStream(uri);
                FileOutputStream out=new FileOutputStream(tmp)){
                if(in==null)throw new IllegalArgumentException("Could not open the selected document");
                byte[] buf=new byte[32768];
                long size=0;int n;
                while((n=in.read(buf))!=-1){
                    size+=n;
                    if(size>80L*1024*1024)throw new IllegalArgumentException("NMAP exceeds 80 MiB");
                    out.write(buf,0,n);
                }
                if(size<40)throw new IllegalArgumentException("Selected file is not an NMAP");
                out.getFD().sync();
                java.nio.file.Files.move(tmp.toPath(),mapFile().toPath(),
                    java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                runOnUiThread(this::openMap);
            }catch(Exception e){
                tmp.delete();
                runOnUiThread(()->status.setText("Import failed: "+e.getMessage()));
            }
        }).start();
    }
    private void openMap(){
        status.setText("Loading 3D mesh...");
        new Thread(()->{
            try{
                NmapView view=new NmapView(this,mapFile());
                runOnUiThread(()->{mapView=view;setContentView(view);});
            }catch(Exception e){
                runOnUiThread(()->status.setText("Map load failed: "+e.getMessage()));
            }
        }).start();
    }
    @Override protected void onPause(){
        if(mapView!=null)mapView.onPause();
        super.onPause();
    }
    @Override protected void onResume(){
        super.onResume();
        if(mapView!=null)mapView.onResume();
    }
    @Override public void onBackPressed(){
        launching=false;
        if(mapView!=null){menu();return;}
        menu();
    }
}
