<?

/*
This is example codes that is calling python scripts.
*/



/*====================================================*/
/*                 smart_resize_image.py              */
/*====================================================*/
    foreach(glob($PIC_DIR.'/' . "*") as $picinput)
    {
        //php GD takes so much memory for resizing. This cases issue on VPS.
        //so here I add py to do resizing.
        $rawImgArr = array(
            "imgFile"   => str_replace("'","&#39;",str_replace("Õ","",$picinput)),
            "imgFileOut" => str_replace("'","&#39;",str_replace("Õ","",$PIC_DIR_RESIZE)),
            "width"      => $IMG_DIPLAY_WIDTH,
            "height"     => 0
        );
        
        $infoImgJson = json_encode($rawImgArr);
        #this required on dreamhost's vps shit!!
        putenv("PYTHONPATH=:/lib/python:/home/cmsbuild/lib/python");
        
        #python smart_resize_image.py '{"imgFile":"../data/GB/pictures/london/Black_London_Cab.jpg","imgFileOut":"../data/GB/pictures/london_resize/","width":"300","height":"300"}'
        $retrun = exec("python script/smart_resize_image.py '$infoImgJson' 2>&1");
        if($retrun == 'ok'){
            foreach(glob($PIC_DIR_RESIZE."*") as $input)
            {
                //we crop the pictures based on UI size.
                resize_image($input, $thumbnail.basename($input), $THUMBNAIL_WIDTH, $THUMBNAIL_HEIGHT, $type = 1, $JPG_QUALITY);
            }
        }
        else
        {
            print("<br>smart_resize_image has error: ".$retrun."<br>");
        }
    }

    
    
    
    
/*====================================================*/
/*                   wikiinfoupdate.py                */
/*====================================================*/
    //locationname, updatewikiurl_submit
    if(isset($_GET['newwikiurl']) & isset($_GET['geonameId']))
    {  
        $newWikiUrl = $_GET['newwikiurl'];
        $geonameId = $_GET['geonameId'];
        $rawArr = array(
                "newWikiUrl" => $newWikiUrl,
                "geonameId"     => $geonameId,
        );
        $infoJson = json_encode($rawArr);
        
        #this required on dreamhost's vps shit!!
        putenv("PYTHONPATH=:/lib/python:/home/cmsbuild/lib/python");
        
        #$ python wikiinfoupdate.py '{"geonameId":"6615354","newWikiUrl":"http://en.wikipedia.org/wiki/Legoland_Windsor_Resort"}'
        $retrun = exec("python script/wikiinfoupdate.py '$infoJson' 2>&1");
        
        if($retrun == 'ok'){
            print 'ok'; //ajax will hear this
        }        
    }
    
    
    
    
/*====================================================*/
/*                   addattraction.py                 */
/*====================================================*/
    if(isset($_POST['attractionwikiurldata']) && isset($_POST['countrycode']))
    {  
        $newWikiUrl = $_POST['attractionwikiurldata'];
        $countrycode = $_POST['countrycode'];
        $locationname = $_POST['locationname'];
        
        $rawArr = array(
                "newWikiUrl" => str_replace("'","&#39;",$newWikiUrl),
                "countrycode" => $countrycode,
                "locationName" => str_replace("'","&#39;",$locationname)
        );
        $infoJson = json_encode($rawArr);
        #this required on dreamhost's vps shit!!
        putenv("PYTHONPATH=:/lib/python:/home/cmsbuild/lib/python");
        
        #$python addattraction.py '{"countrycode":"GB","newWikiUrl":"http://en.wikipedia.org/wiki/Adventure_Wonderland","locationName":"Adventure Wonderland"}'
        $retrun = exec("python script/addattraction.py '$infoJson' 2>&1");
        
        if($retrun == 'ok'){
            print 'ok'; //ajax will hear this
        }
    }
    
    
    
    
/*====================================================*/
/*                   getwikiimage.py                 */
/*====================================================*/
    if(isset($_POST['wikiurl']))
    {
        #this required on dreamhost's vps shit!!
        putenv("PYTHONPATH=:/lib/python:/home/cmsbuild/lib/python");
        
        $locationName = basename($_POST['wikiurl']);
        $retrun = exec("python script/getwikiimage.py $locationName", $out, $rc);
        
        if($rc == 0){
            $callback = '1';
        } else {
            $callback = '0';
        }
        $data = json_decode($retrun);
                
        if(empty($data->images))
        {
            echo("No images are in wiki yet.");
        }
        else
        {
            foreach($data->images as $ele)
            {
                echo '<div id="cell" class="">';
                echo "<ul>";
                echo "<li>"
                    ."<p><a href='". $ele->imgDescriptionUrl ."' target='_blank'>". basename($ele->imgDownLoadUrl) . "</a></p>" 
                    ."<div class='imgdiv'><img class='imgtarget' src='". $ele->imgDownLoadUrl . "' width='300'></div>"
                    ."<input type='hidden' name='' class='imginput' value=". $ele->imgDownLoadUrl .">"
                    ."<input type='hidden' name='' value='". basename($ele->imgDownLoadUrl) . "'>"
                    ."<p><textarea class='imgtextarea' row='3' name=''>" . $ele->imgDescription . "</textarea></p>" 
                    ."</li>";
                echo "</ul>";
                echo "</div>";
            } 
        }
    }


    
    