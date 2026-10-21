package org.bitflipunix.nuke;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.graphics.Color;
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
        button("PLAY OFFLINE BLOCKOUT",root).setOnClickListener(v->setContentView(new ArenaView(this)));
        button("IMPORT EXPORTED NUKETOWN .NMAP",root).setOnClickListener(v->choose());
        Button open=button("EXPLORE IMPORTED MAP (3D)",root);
        open.setEnabled(mapFile().isFile());
        open.setOnClickListener(v->openMap());
        setContentView(root);
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
        if(mapView!=null){menu();return;}
        menu();
    }
}
