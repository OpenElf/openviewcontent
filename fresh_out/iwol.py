
import sys, os, re, urllib, urllib2
import xbmc,xbmcplugin,xbmcgui,xbmcaddon

#import cookielib

import jsunpack
import myutils
import metarequest
import resolvers


# Use addon common library for http calls
try:
    from addon.common.net import Net
    from addon.common.addon import Addon
except:
    xbmc.log('Failed to import script.module.addon.common')
    xbmcgui.Dialog().ok("OpenView HD Import Failure", "Failed to import \
        addon.common", "A component needed by OpenView is missing on your \
        system", "Please contact openviewhelp@gmail.com for help")

net = Net()

addon_id = 'plugin.video.openviewhd'
addon = Addon(addon_id, sys.argv)

base_url = 'http://www.iwatchonline.to/'
search_url = 'http://www.iwatchonline.to/search'


DEBUG = addon.get_setting('debug')

def featured_films():
    base_page_list = scrape_base_url(base_url)
    # A list of contextmenu items
    contextMenuItems = []
    # HD latest is [1]
    for page_url, title in base_page_list[0]:
        # for progress bar
        totalitems = 6

        display_title = title

        # i think title needs to change from ( 2014 ) to (2014) so
        title = re.sub(r'(\s(\d{4})\s)',r'\g<2>', title)

#        title = title.decode('UTF-8','ignore') 

       

        meta_params = metarequest.make_meta_params(title)

        if DEBUG == 'true':
            addon.log('--- default.py featured_films function has just received meta_params ---')
            for key, value in meta_params.items():
                addon.log('--- %s, %s' %(key, value))

        # build non playable directories to display the six films with meta
        if DEBUG == 'true':
            addon.log('--- building featured_films movie infolabels for: %s' %title)

        # change the movie name to drop the (2014) piece to get meta working
        meta_params['name'] = re.sub(r'\(\d{4}\)',r'',meta_params['name'])
        # the title may not be in Ascii encode it into UTF-8 else methandler will crash  
        meta_params['name'] = meta_params['name'].encode('UTF-8','ignore')
 
     
        infolabels = metarequest.get_infolabels(meta_params)
        
        if DEBUG == 'true':
            addon.log('--- featured_films movie infolabels are: %s' %infolabels)

        # for refresh context menu
        videoType = 'movie'

        # imdb is from infolabels
        imdb = infolabels['imdb_id']

        infolabels['title'] = display_title

        contextMenuItems.append(('[COLOR aqua]Refresh Info[/COLOR]', 'XBMC.RunPlugin(%s?mode=100&name=%s&url=%s&imdbnum=%s&dirmode=%s&videoType=%s)' % (sys.argv[0], title, page_url, imdb, meta_params['category'], videoType)))


         # note this updates 'backdrop' and 'thumb' through queries
                
        addon.add_directory({'mode' : '210' , 'url' : page_url, 'name' : title, 'videoType' : 'Movie', 'imdbnum' : imdb, 'backdrop' : infolabels['backdrop_url'], 'thumb' : infolabels['cover_url']}, infolabels, contextmenu_items = contextMenuItems, total_items=totalitems, img= infolabels['cover_url'], fanart= infolabels['backdrop_url'])

        contextMenuItems.pop()

    return

def top_six():
    base_page_list = scrape_base_url(base_url)
    # A list of contextmenu items
    contextMenuItems = []
    # HD latest is [1]
    for page_url, title in base_page_list[1]:
        # for progress bar
        totalitems = 6

        display_title = title

        # i think title needs to change from ( 2014 ) to (2014) so
        title = re.sub(r'(\s(\d{4})\s)',r'\g<2>', title)

        meta_params = metarequest.make_meta_params(title)

        if DEBUG == 'true':
            addon.log('--- default.py top_six function has just received meta_params ---')
            for key, value in meta_params.items():
                addon.log('--- %s, %s' %(key, value))

        # build non playable directories to display the six films with meta
        if DEBUG == 'true':
            addon.log('--- building top_six movie infolabels for: %s' %title)

        # change the movie name to drop the (2014) piece to get meta working
        meta_params['name'] = re.sub(r'\(\d{4}\)',r'',meta_params['name'])
        # the title may not be Ascii so encode into UTF-8 
        meta_params['name'] = meta_params['name'].encode('UTF-8','ignore')     
     
        infolabels = metarequest.get_infolabels(meta_params)
        
        if DEBUG == 'true':
            addon.log('--- top_six movie infolabels are: %s' %infolabels)

        # for refresh context menu
        videoType = 'movie'

        # imdb is from infolabels
        imdb = infolabels['imdb_id']

        infolabels['title'] = display_title

        contextMenuItems.append(('[COLOR aqua]Refresh Info[/COLOR]', 'XBMC.RunPlugin(%s?mode=100&name=%s&url=%s&imdbnum=%s&dirmode=%s&videoType=%s)' % (sys.argv[0], title, page_url, imdb, meta_params['category'], videoType)))


         # note this updates 'backdrop' and 'thumb' through queries
                
        addon.add_directory({'mode' : '210' , 'url' : page_url, 'name' : title, 'videoType' : 'Movie', 'imdbnum' : imdb, 'backdrop' : infolabels['backdrop_url'], 'thumb' : infolabels['cover_url']}, infolabels, contextmenu_items = contextMenuItems, total_items=totalitems, img= infolabels['cover_url'], fanart= infolabels['backdrop_url'])

        contextMenuItems.pop()

    return



def search_films():
# search for a film and return a match object of possible films
# match object - thumb, url, name
    try:

        # A list of contextmenu items
        contextMenuItems = []
        # add refresh context menu
        videoType = 'movie'
        # get the search query from user
        keyb = xbmc.Keyboard('', 'OpenView Film Search' )
        keyb.doModal()
        if (keyb.isConfirmed()):
            iwol_query = keyb.getText()
        else:
            xbmcplugin.endOfDirectory(int(sys.argv[1]),False,False)
            return False

        
        resp = net.http_GET(base_url)
        search_content = net.http_POST(search_url, { 'searchquery' : iwol_query, 'searchin' : 'm'} ).content.encode('utf-8')
        # first we get the html table that houses all the possible options returned from the search
        dirty_html = re.findall('(?s)<table(.+?)</table>',search_content)
        clean_html = myutils.clean(dirty_html[0])
        # now we get a thumbnail, url and name for each possible option
        match = re.compile('<img.+?src=\"(.+?)\".+?<a.+?href=\"(.+?)\">(.+?)</a>').findall(clean_html)


        dialogWait = xbmcgui.DialogProgress()
        ret = dialogWait.create('Please wait until Film list is cached.')
        totalitems = len(match)
        loadedLinks = 0
        remaining_display = 'Films loaded :: [B]'+str(loadedLinks)+' / '+str(totalitems)+'[/B].'
        dialogWait.update(0,'[B]Will load instantly from now on[/B]',remaining_display)
        xbmc.executebuiltin("XBMC.Dialog.Close(busydialog,true)")
        for thumb,url,name in match:
            
            addon.log('--- The possible film matches are %s, %s, %s' %(thumb, url, name))

            meta_params = metarequest.make_meta_params(name)

            # change the film name to drop the (2014) piece to get meta working
            meta_params['name'] = re.sub(r'\(\d{4}\)',r'',meta_params['name']) 

            infolabels = metarequest.get_infolabels(meta_params)
            # put original film name back for display
            infolabels['title'] = '[COLOR aqua]'+name+'[/COLOR]'

            contextMenuItems.append(('[COLOR aqua]Refresh Info[/COLOR]', 'XBMC.RunPlugin(%s?mode=100&name=%s&url=%s&imdbnum=%s&dirmode=%s&videoType=%s)' % (sys.argv[0], name, url, infolabels['imdb_id'], meta_params['category'], videoType)))

                    # note this updates 'backdrop' and 'thumb' through queries
                
            addon.add_directory({'mode' : '210' , 'url' : url, 'name' : name, 'videoType' : 'Movie', 'imdbnum' : infolabels['imdb_id'], 'backdrop' : infolabels['backdrop_url'], 'thumb' : infolabels['cover_url']}, infolabels, contextmenu_items = contextMenuItems, total_items=totalitems, img= infolabels['cover_url'], fanart= infolabels['backdrop_url'])

            contextMenuItems.pop()

            loadedLinks = loadedLinks + 1
            percent = (loadedLinks * 100)/totalitems
            remaining_display = 'Films loaded :: [B]'+str(loadedLinks)+' / '+str(totalitems)+'[/B].'
            dialogWait.update(percent,'[B]Will load instantly from now on[/B]',remaining_display)
            if dialogWait.iscanceled(): return False   
        dialogWait.close()
        del dialogWait        
      
    except Exception, e:
        addon.log('**** There was a film search error: %s' %e)
        raise
    return match

def search_tv():
# iwol for a tv show and return a match object of possible shows
# match object - thumb, url, name

    try:

        # A list of contextmenu items
        contextMenuItems = []
        # add refresh context menu
        videoType = 'tvshow'
        # get the iwol query from user
        keyb = xbmc.Keyboard('', 'OpenView TV show Search' )
        keyb.doModal()
        if (keyb.isConfirmed()):
            iwol_query = keyb.getText()
        else:
            xbmcplugin.endOfDirectory(int(sys.argv[1]),False,False)
            return False

        
        resp = net.http_GET(base_url)
        search_content = net.http_POST(search_url, { 'searchquery' : iwol_query, 'searchin' : 't'} ).content.encode('utf-8')
        # first we get the html table that houses all the possible options returned from the search
        dirty_html = re.findall('(?s)<table(.+?)</table>',search_content)
        clean_html = myutils.clean(dirty_html[0])
        # now we get a thumbnail, url and name for each possible option
        match = re.compile('<img[^>]+?src="([^"]+?)\".+?<a[^>]+?href="([^"]+?)">([^<]+?)</a>').findall(clean_html)

        dialogWait = xbmcgui.DialogProgress()
        ret = dialogWait.create('Please wait until TV show list is cached.')
        totalitems = len(match)
        loadedLinks = 0
        remaining_display = 'TV shows loaded :: [B]'+str(loadedLinks)+' / '+str(totalitems)+'[/B].'
        dialogWait.update(0,'[B]Will load instantly from now on[/B]',remaining_display)
        xbmc.executebuiltin("XBMC.Dialog.Close(busydialog,true)")

        for thumb,url,name in match:

            if DEBUG == 'true':
                  addon.log('--- iwol possible TV matches are %s, %s, %s' %(thumb, url, name))

            original_name = name

            # change the TV show to drop the (2014) piece to get meta working
            name = re.sub(r'\(\d{4}\)',r'', name)

            meta_params = metarequest.make_meta_params(name)

            infolabels = metarequest.get_infolabels(meta_params)

            # change how the title is displayed
            infolabels['title'] = '[COLOR aqua]'+original_name+'[/COLOR]'

            contextMenuItems.append(('[COLOR aqua]Refresh Info[/COLOR]', 'XBMC.RunPlugin(%s?mode=100&name=%s&url=%s&imdbnum=%s&dirmode=%s&videoType=%s)' % (sys.argv[0], name, url, infolabels['imdb_id'], meta_params['category'], videoType)))


            # note this updates 'backdrop' and 'thumb' through queries.
                
            addon.add_directory({'mode' : '202' , 'url' : url, 'name' : original_name, 'videoType' : 'TV Show', 'imdbnum' : infolabels['imdb_id'], 'backdrop' : infolabels['backdrop_url'], 'thumb' : infolabels['cover_url']}, infolabels, contextmenu_items = contextMenuItems, total_items=totalitems, img= infolabels['cover_url'], fanart= infolabels['backdrop_url'])

            contextMenuItems.pop()

            loadedLinks = loadedLinks + 1
            percent = (loadedLinks * 100)/totalitems
            remaining_display = 'TV shows loaded :: [B]'+str(loadedLinks)+' / '+str(totalitems)+'[/B].'
            dialogWait.update(percent,'[B]Will load instantly from now on[/B]',remaining_display)
            if dialogWait.iscanceled(): return False   
        dialogWait.close()
        del dialogWait        
      
    except Exception, e:
        addon.log('**** There was a TV manual search error in iwol: %s' %e)
        raise
    return match



def film_streams(title,url,backdrop,thumb):
# display a list of streams from scraping a url

    original_title = title

    dialog = xbmcgui.Dialog()
    line1 = '[COLOR yellow]GOLD STREAM:     HD may buffer at peak times[/COLOR]'
    line2 = '[COLOR white]SILVER STREAM:   SD standard definition[/COLOR]'
    line3 = '[COLOR orange]BRONZE STREAM:  LQ lower quality[/COLOR]'
    ok=dialog.ok('[B]SELECT STREAM QUALITY[/B]', str(line1) ,str(line2),str(line3))
 
    media_url_list = scrape_media_film_url(url)
    
    if not media_url_list:
        dialog = xbmcgui.Dialog()
        line1 = '[COLOR red]Problem with '+title+ ' .[/COLOR]'
        line2 = '[COLOR lime]There are no good quality streams for your selection.[/COLOR]'
        line3 = '[COLOR aqua]We cannot do anything about this.[/COLOR]'
        ok=dialog.ok('[B]Content Announcement[/B]', str(line1) ,str(line2),str(line3))

        dialog = xbmcgui.Dialog()
        line1 = '[COLOR lime]You will see a blank screen when you click the OK button.[/COLOR]'
        line2 = '[COLOR lime]Use the back key to return to your previous menu.[/COLOR]'
        line3 = '[COLOR lime]Then select some other choice from the menu. [/COLOR]'
        ok=dialog.ok('[B]Content Announcement[/B]', str(line1) ,str(line2),str(line3))
        
        if DEBUG == 'true':
            addon.log('--- No streams found for iwol selection: %s' %title)
        return       
    totalitems = len(media_url_list)
    stream_type = '[COLOR lime] HD [/COLOR]'
    count = 1

    for media_url in media_url_list:
        host_server=re.search('http://(.+?)/.+?' , media_url)
        # it is possible for the regex search to fail so handle that scenario explicitly

        if host_server is not None:
            host_name = host_server.group(1)
            host_name = host_name.replace('www.','').replace('.in','').replace('.net','').replace('.com','').replace('.to','').replace('.org','').replace('.ch','').replace('.sx','').replace('.se','').replace('.es','').lower()
           # host_name = '[COLOR blue]'+host_name+'[/COLOR]'

            # map host_name to service i.e firedrive maps to GOLD
            if host_name == 'sockshare' or host_name == 'firedrive' or host_name == 'billionuploads' or host_name == 'movreel':
                host_name = '[COLOR yellow]'+ 'GOLD STREAM' +'[/COLOR]'
            elif host_name == 'allmyvideos' or host_name == 'promptfile' or host_name == 'nowvideo' or host_name == 'movdivx' or host_name == 'videoweed':
                host_name = '[COLOR white]'+ 'SILVER STREAM' +'[/COLOR]'
            elif host_name == 'vodlocker' or host_name == 'played' or host_name == 'daclips' or host_name == 'gorillavid':
                host_name = '[COLOR orange]'+ 'BRONZE STREAM' +'[/COLOR]'
            else:
                host_name = '[COLOR blue]'+host_name+'[/COLOR]'

        if host_server is None:
            host_name = '[COLOR red]EMPTY[/COLOR]'


        stream = '[COLOR yellow]Stream%d   [/COLOR]' % (count,)
        title = '[COLOR aqua]'+title+'[/COLOR]' 
        title = stream + title + stream_type + host_name

        # using 'dirmode' for stream type
        addon.add_item({'mode' : '7' , 'url' : media_url, 'name' : title, 'videoType' : 'Movie', 'dirmode' : stream_type, 'season' : stream, 'backdrop' : backdrop, 'thumb' : thumb}, {'title':  title}, total_items=totalitems, img= thumb, fanart= backdrop)

        title = original_title

        count = count + 1      

    return

def tv_streams(title,url,backdrop,thumb):
# # display a list of streams from scraping a url

    original_title = title

    dialog = xbmcgui.Dialog()
    line1 = '[COLOR yellow]GOLD STREAM:     HD may buffer at peak times[/COLOR]'
    line2 = '[COLOR white]SILVER STREAM:   SD standard definition[/COLOR]'
    line3 = '[COLOR orange]BRONZE STREAM:  LQ lower quality[/COLOR]'
    ok=dialog.ok('[B]SELECT STREAM QUALITY[/B]', str(line1) ,str(line2),str(line3))
 
    media_url_list = scrape_media_tv_url(url)


    if DEBUG == 'true':
        addon.log('--- Scraped media TV url: %s' %media_url_list)
    
    if not media_url_list:
        dialog = xbmcgui.Dialog()
        line1 = '[COLOR red]Problem with '+title+ ' .[/COLOR]'
        line2 = '[COLOR aqua]Either there are no good quality streams for your[/COLOR]'
        line3 = '[COLOR aqua]selection or the show has not aired yet.[/COLOR]'
        ok=dialog.ok('[B]Content Announcement[/B]', str(line1) ,str(line2),str(line3))

        dialog = xbmcgui.Dialog()
        line1 = '[COLOR lime]You will see a blank screen when you click the OK button.[/COLOR]'
        line2 = '[COLOR lime]Use the back key to return to your previous menu.[/COLOR]'
        line3 = '[COLOR lime]Then select some other choice from the menu. [/COLOR]'
        ok=dialog.ok('[B]Content Announcement[/B]', str(line1) ,str(line2),str(line3))
        
        if DEBUG == 'true':
            addon.log('--- No streams found for iwol selection: %s' %title)
        return       
    totalitems = len(media_url_list)
    stream_type = '[COLOR lime] HDTV [/COLOR]'
    count = 1

    for media_url in media_url_list:
        host_server=re.search('http://(.+?)/.+?' , media_url)
        # it is possible for the regex search to fail so handle that scenario explicitly

        if host_server is not None:
            host_name = host_server.group(1)
            host_name = host_name.replace('www.','').replace('.in','').replace('.net','').replace('.com','').replace('.to','').replace('.org','').replace('.ch','').replace('.sx','').replace('.se','').replace('.es','').lower()
            #host_name = '[COLOR blue]'+host_name+'[/COLOR]'
            # map host_name to service i.e firedrive maps to GOLD
            if host_name == 'sockshare' or host_name == 'firedrive' or host_name == 'billionuploads' or host_name == 'movreel':
                host_name = '[COLOR yellow]'+ 'GOLD STREAM' +'[/COLOR]'

            if host_name == 'billionuploads' or host_name == 'movreel':
                host_name = '[COLOR yellow]'+ 'GOLD STREAM' +'[/COLOR]'



            elif host_name == 'allmyvideos' or host_name == 'promptfile' or host_name == 'nowvideo' or host_name == 'movdivx' or host_name == 'videoweed':
                host_name = '[COLOR white]'+ 'SILVER STREAM' +'[/COLOR]'
            elif host_name == 'vodlocker' or host_name == 'played' or host_name == 'daclips' or host_name == 'gorillavid':
                host_name = '[COLOR orange]'+ 'BRONZE STREAM' +'[/COLOR]'
            else:
                host_name = '[COLOR blue]'+host_name+'[/COLOR]'

        if host_server is None:
            host_name = '[COLOR red]EMPTY[/COLOR]'


        stream = '[COLOR yellow]Stream%d   [/COLOR]' % (count,)
        title = '[COLOR aqua]'+title+'[/COLOR]'              
        title = stream + title + stream_type + host_name

        # using 'dirmode' for stream type
        addon.add_item({'mode' : '7' , 'url' : media_url, 'name' : title, 'videoType' : 'Movie', 'dirmode' : stream_type, 'season' : stream, 'backdrop' : backdrop, 'thumb' : thumb}, {'title':  title}, total_items=totalitems, img= thumb, fanart= backdrop)

        title = original_title

        count = count + 1      

    return

def scrape_media_film_url(page_url):
# return a list of media urls for each title page_url, for example,
# the page_url points to the Matrix that has many host servers delivering the required content
# returns a list of media urls for each title page_url
        try:


            resp = net.http_GET(page_url)
            html = resp.content
            media_url_list = []
            count = 0
            firedrive_count = 0
            allmyvideo_count = 0
            played_count = 0
            vodlocker_count = 0
            nowvideo_count = 0
            movreel_count = 0
            vodlocker_count = 0
            billionuploads_count = 0
            videoweed_count = 0
            played_count = 0
            nowvideo_count = 0
            videoweed_count = 0

            match = re.compile('<a href="(.+?)" target="_blank" rel="nofollow">\s*<img src=".+?" alt="" /> (.+?)\s*<!-- -->\s*</td>\s*<td><img src="http://www.iwatchonline.to/assets/images/English.gif"/ rel="tooltip" data-original-title="English"></td>\s*<td>(.+?)</td>\s*<td>(.+?)</td>').findall(html)
            
            if match:
                    
                    for media_url, host_server, time, quality in match:
                            #
                            
                            if host_server == 'Allmyvideos.net':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                    
                                            
                                            if allmyvideo_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    allmyvideo_count = 1
                            
                            if host_server == 'Firedrive.com':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                            
                                            if firedrive_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    firedrive_count = 1                                  

                            if host_server == 'Sockshare.com':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                            
                                            if count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    count = 1

                            if host_server == 'Movreel.com':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                            
                                            if movreel_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    movreel_count = 1

                            if host_server == 'Vodlocker.com':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                            
                                            if vodlocker_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    vodlocker_count = 1

                            if host_server == 'Billionuploads.com':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                            
                                            if billionuploads_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    billionuploads_count = 1

                            if host_server == 'Played.to':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                            
                                            if played_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    played_count = 1

                            if host_server == '.nowvideo.sx':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                            
                                            if nowvideo_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    nowvideo_count = 1

                            if host_server == '.videoweed.es':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                            
                                            if videoweed_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    videoweed_count = 1
                                    
            else:
                    addon.log('unable to find a media url for the page url %s' % page_url)        
            
        except Exception, e:
            addon.log('**** Scrape Media URL from given Page URL Error occured: %s' % e)
            raise      
        return media_url_list

def scrape_media_tv_url(page_url):
# return a list of media urls for each title page_url, for example,
# the page_url points to the Modern Family that has many host servers delivering
# the required content
# returns a list of media urls for each title page_url
        try:


            resp = net.http_GET(page_url)
            html = resp.content
            clean_html = myutils.clean(html)
            media_url_list = []
            count = 0
            firedrive_count = 0
            allmyvideo_count = 0
            played_count = 0
            vodlocker_count = 0
            nowvideo_count = 0
            movreel_count = 0
            vodlocker_count = 0
            billionuploads_count = 0
            played_count = 0
            videoweed_count = 0

            # first we grab the streamlink table

            streamlink_table = re.search(r'id="streamlinks">  <thead>(.+?)</table>', clean_html)

            # if the streamlink table is not present it is because the programme has not aired

            if not streamlink_table:
                addon.log('--- TV programme has not aired yet : %s' %page_url)
                return

            # now get the media urls

            match = re.compile(r'<tr class=".+?" id=".+?"><td class=".+?"><a href="(.+?)" target="_blank" rel="nofollow"><img src=".+?" alt="" />\s*(.+?)</td>\s*<td><img src=".+?"/ rel=".+?" data-original-title="English"></td>\s*<td><span class="linkdate">.+?</span></td>\s*<td>(.+?)</td>').findall(streamlink_table.group())



            if match:
                    
                    for media_url, host_server, quality in match:
                            if DEBUG == 'true':
                                addon.log('--- TV media_url : %s' %media_url) 
                                addon.log('--- TV host_server : %s' %host_server)
                                addon.log('--- TV quality : %s' %quality)
                            
                            if host_server == 'Allmyvideos.net':
                                    
                                    if quality == 'HD' or quality == 'HDTV':
                                    
                                            
                                            if allmyvideo_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    # ensure correct title in header, for example,
                                                    # this is bad <title> - iwatchonline.to</title>
                                                    # but this is good <title>Extant - iwatchonline.to</title>

                                                    title_html = re.search(r'<head>\s*<meta charset="utf-8">\s*<title>(.+?)</title>', html)
                                                    title_html = title_html.group(1).replace(" ","")
                                                    title_split = title_html.split('-')

                                                    # only look for a media url if the html title tag was correctly formed
                                                    if title_split[0]:

                                                        r = re.findall(r'<iframe name="frame" class="frame" src="(.+?)"\s*allowtransparency="true" >\s*</iframe>',html)
                                                        media_url = r[0]
                                                        media_url_list.append(media_url)
                                                        allmyvideo_count = 1
                            
                            if host_server == '.firedrive.com':
                                    
                                    if quality == 'HD' or quality == 'HDTV':
                                   
                                            
                                            if firedrive_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    # ensure correct title in header, for example,
                                                    # this is bad <title> - iwatchonline.to</title>
                                                    # but this is good <title>Extant - iwatchonline.to</title>

                                                    title_html = re.search(r'<head>\s*<meta charset="utf-8">\s*<title>(.+?)</title>', html)
                                                    title_html = title_html.group(1).replace(" ","")
                                                    title_split = title_html.split('-')

                                                    # only look for a media url if the html title tag was correctly formed
                                                    if title_split[0]:
                                                        r = re.findall(r'<iframe name="frame" class="frame" src="(.+?)"\s*allowtransparency="true" >\s*</iframe>',html)
                                                        media_url = r[0]
                                                        media_url_list.append(media_url)
                                                        firedrive_count = 1                                  

                            if host_server == '.sockshare.com':
                                    
                                    if quality == 'HD' or quality == 'HDTV':
                                            
                                            if count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    # ensure correct title in header, for example,
                                                    # this is bad <title> - iwatchonline.to</title>
                                                    # but this is good <title>Extant - iwatchonline.to</title>

                                                    title_html = re.search(r'<head>\s*<meta charset="utf-8">\s*<title>(.+?)</title>', html)
                                                    title_html = title_html.group(1).replace(" ","")
                                                    title_split = title_html.split('-')

                                                    # only look for a media url if the html title tag was correctly formed
                                                    if title_split[0]:
                                                        r = re.findall(r'<iframe name="frame" class="frame" src="(.+?)"\s*allowtransparency="true" >\s*</iframe>',html)
                                                        media_url = r[0]
                                                        media_url_list.append(media_url)
                                                        count = 1

                            if host_server == 'Movreel.com':
                                    
                                    if quality == 'HD' or quality == 'HDTV':
                                            
                                            if movreel_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    # ensure correct title in header, for example,
                                                    # this is bad <title> - iwatchonline.to</title>
                                                    # but this is good <title>Extant - iwatchonline.to</title>

                                                    title_html = re.search(r'<head>\s*<meta charset="utf-8">\s*<title>(.+?)</title>', html)
                                                    title_html = title_html.group(1).replace(" ","")
                                                    title_split = title_html.split('-')

                                                    # only look for a media url if the html title tag was correctly formed
                                                    if title_split[0]:
                                                        r = re.findall(r'<iframe name="frame" class="frame" src="(.+?)"\s*allowtransparency="true" >\s*</iframe>',html)
                                                        media_url = r[0]
                                                        media_url_list.append(media_url)
                                                        movreel_count = 1

                            if host_server == 'Vodlocker.com':
                                    
                                    if quality == 'HD' or quality == 'HDTV':
                                            
                                            if vodlocker_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    # ensure correct title in header, for example,
                                                    # this is bad <title> - iwatchonline.to</title>
                                                    # but this is good <title>Extant - iwatchonline.to</title>

                                                    title_html = re.search(r'<head>\s*<meta charset="utf-8">\s*<title>(.+?)</title>', html)
                                                    title_html = title_html.group(1).replace(" ","")
                                                    title_split = title_html.split('-')

                                                    # only look for a media url if the html title tag was correctly formed
                                                    if title_split[0]:

                                                    
                                                        r = re.findall(r'<iframe name="frame" class="frame" src="(.+?)"\s*allowtransparency="true" >\s*</iframe>',html)

                                                        media_url = r[0]
                                                        media_url_list.append(media_url)
                                                        vodlocker_count = 1

                            if host_server == 'Billionuploads.com':
                                    
                                    if quality == 'HD' or quality == 'HDTV':
                                            
                                            if billionuploads_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    # ensure correct title in header, for example,
                                                    # this is bad <title> - iwatchonline.to</title>
                                                    # but this is good <title>Extant - iwatchonline.to</title>

                                                    title_html = re.search(r'<head>\s*<meta charset="utf-8">\s*<title>(.+?)</title>', html)
                                                    title_html = title_html.group(1).replace(" ","")
                                                    title_split = title_html.split('-')

                                                    # only look for a media url if the html title tag was correctly formed
                                                    if title_split[0]:
                                                        r = re.findall(r'<iframe name="frame" class="frame" src="(.+?)"\s*allowtransparency="true" >\s*</iframe>',html)
                                                        media_url = r[0]
                                                        media_url_list.append(media_url)
                                                        billionuploads_count = 1

                            if host_server == 'Played.to':
                                    
                                    if quality == 'HD' or quality == 'HDTV':
                                            
                                            if played_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    # ensure correct title in header, for example,
                                                    # this is bad <title> - iwatchonline.to</title>
                                                    # but this is good <title>Extant - iwatchonline.to</title>

                                                    title_html = re.search(r'<head>\s*<meta charset="utf-8">\s*<title>(.+?)</title>', html)
                                                    title_html = title_html.group(1).replace(" ","")
                                                    title_split = title_html.split('-')

                                                    # only look for a media url if the html title tag was correctly formed
                                                    if title_split[0]:
                                                        r = re.findall(r'<iframe name="frame" class="frame" src="(.+?)"\s*allowtransparency="true" >\s*</iframe>',html)
                                                        media_url = r[0]
                                                        media_url_list.append(media_url)
                                                        played_count = 1

                            if host_server == '.nowvideo.sx':
                                    
                                    if quality == 'HD' or quality == 'HDTV':
                                            
                                            if nowvideo_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    # ensure correct title in header, for example,
                                                    # this is bad <title> - iwatchonline.to</title>
                                                    # but this is good <title>Extant - iwatchonline.to</title>

                                                    title_html = re.search(r'<head>\s*<meta charset="utf-8">\s*<title>(.+?)</title>', html)
                                                    title_html = title_html.group(1).replace(" ","")
                                                    title_split = title_html.split('-')

                                                    # only look for a media url if the html title tag was correctly formed
                                                    if title_split[0]:
                                                        r = re.findall(r'<iframe name="frame" class="frame" src="(.+?)"\s*allowtransparency="true" >\s*</iframe>',html)
                                                        media_url = r[0]
                                                        media_url_list.append(media_url)
                                                        nowvideo_count = 1

                            if host_server == '.videoweed.es':
                                    
                                    if quality == 'HD' or quality == 'HDTV':
                                            
                                            if videoweed_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    # ensure correct title in header, for example,
                                                    # this is bad <title> - iwatchonline.to</title>
                                                    # but this is good <title>Extant - iwatchonline.to</title>

                                                    

                                                    title_html = re.search(r'<head>\s*<meta charset="utf-8">\s*<title>(.+?)</title>', html)
                                                    title_html = title_html.group(1).replace(" ","")
                                                    title_split = title_html.split('-')

                                                    # only look for a media url if the html title tag was correctly formed
                                                    if title_split[0]:
                                                        r = re.findall(r'<iframe name="frame" class="frame" src="(.+?)"\s*allowtransparency="true" >\s*</iframe>',html)
                                                        media_url = r[0]
                                                        media_url_list.append(media_url)
                                                        videoweed_count = 1
                                    
            else:
                    addon.log('unable to find any TV media urls for the page url %s' % page_url)

   
        except Exception, e:
            addon.log('**** Scrape Media URL from given TV Page URL Error occured: %s' % e)
            raise      
        return media_url_list

def search_tv_season(name,url,backdrop,thumb):

    try:
        resp = net.http_GET(url)
        html = resp.content
        clean_html = myutils.clean(html)
        match=re.compile('<h5><i.+?</i>.*?(.+?)</h5>').findall(clean_html)
        totalitems = len(match)
        if match:
            for season in match:
            # using 'dirmode' to maintain the name of the TV Show for use in tv_episode meta handling

                addon.add_directory({'mode' : '204' , 'url' : url, 'name' : name, 'videoType' : 'TV Show', 'backdrop' : backdrop, 'thumb' : thumb, 'season' : season, 'dirmode' : name}, {'title': '[COLOR aqua]'+name+'[/COLOR]''[COLOR yellow]'+season+'[/COLOR]'}, total_items=totalitems, img =  thumb, fanart = backdrop) 
        else:
            addon.log('Problem finding TV season from url %s' % url) 

    except Exception, e:
        addon.log('**** Unable to find TV season for given url: %s' % e)
        raise 

    return

def search_tv_episode(name,season_num,url,backdrop,thumb,dirmode):

    try:
        season_num = season_num.lstrip()
        resp = net.http_GET(url)
        html = resp.content
        clean_html = myutils.clean(html)
        season_int = season_num.split('Season ')[1]
        # first we grab the relevant season table
        episodes = re.search('</i>  '+season_num+'</h5>(.+?)</table>', clean_html)
        # next we get the episodes for the relevant season
        if episodes:

            episodes = episodes.group(1)
#            match=re.compile('<a[^>]+?href=\"([^"]+?)\".+?</i>([^<]+?)</a>.+?<td>([^<]+?)</td>').findall(episodes)

            match=re.compile('<a href="(.+?)"><i class="icon-play-circle"></i> (.+?)</a></td>  <td>(.+?)</td>').findall(episodes)




            dialogWait = xbmcgui.DialogProgress()
            ret = dialogWait.create('Your TV episodes are now being collected.')
            totalLinks = len(match)
            loadedLinks = 0
            remaining_display = 'Episodes loaded :: [B]'+str(loadedLinks)+' / '+str(totalLinks)+'[/B].'
            dialogWait.update(0,'[B]The episodes will be loaded a little quicker from now on[/B]',remaining_display)
            for url,epi,name in match:

                if DEBUG == 'true':
                    addon.log('--- TV episode name : %s' %name)  
                    addon.log('--- TV episode number : %s' %epi)  
                    addon.log('--- TV episode url : %s' %url)    
                # build the meta data for each episode within the season
                episode_int = epi.split('Episode ')[1]
                name = name.split('(')[0]
                dirmode = dirmode.split('(')[0]
                meta_params_name = dirmode +'S'+season_int+'E'+episode_int

                # example name Extant S01E01, Extant S01E02 etc season held constant, episode increments
                meta_params = metarequest.make_meta_params(meta_params_name)
                infolabels = metarequest.get_infolabels(meta_params)

                # change how the title is displayed
                infolabels['title'] = '[COLOR yellow]'+meta_params_name+'[/COLOR] : ' + '[COLOR aqua]'+infolabels['title']+'[/COLOR]'
                    # add refresh context menu
                videoType = 'tvshow' # meta_parms['category']

                #    contextMenuItems.append(('[COLOR aqua]Refresh Info[/COLOR]', 'XBMC.RunPlugin(%s?mode=100&name=%s&url=%s&imdbnum=%s&dirmode=%s&videoType=%s)' % (sys.argv[0], title, url, imdb, meta_params['category'], videoType)))


                    # note this updates 'backdrop' and 'thumb' through queries
                
                addon.add_directory({'mode' : '211' , 'url' : url, 'name' : name, 'videoType' : 'TV Show', 'backdrop' : infolabels['backdrop_url'], 'thumb' : infolabels['cover_url']}, infolabels, total_items=totalLinks, img= infolabels['cover_url'], fanart= infolabels['backdrop_url'])



              #      contextMenuItems.pop()




             
                


                loadedLinks = loadedLinks + 1
                percent = (loadedLinks * 100)/totalLinks
                remaining_display = 'Episodes loaded :: [B]'+str(loadedLinks)+' / '+str(totalLinks)+'[/B].'
                dialogWait.update(percent,'[B]Will load instantly from now on[/B]',remaining_display)
                if (dialogWait.iscanceled()):
                    return False   
            dialogWait.close()
            del dialogWait


        else:
            addon.log('Problem finding a match for TV episodes from url %s' % url) 

    except Exception, e:
        addon.log('**** Unable to find TV episode for given url: %s' % e)
        raise 

    return

def scrape_base_url(base_url):
# scrapes the home page of iwatchonline and 
# returns three lists within a list. Each list has six elements.
# Featured movies (6) Latest HD Movies (6) and Featured Shows (6)
# 
        try:
            resp = net.http_GET(base_url)
            html = resp.content
            r = re.findall(r'<li class="span2">\s*<a href="(.+?)" class="thumbnail" title="(.+?)" rel="tooltip">', html)
            # chunks is a list of lists, the first six are featured movies etc
            base_page_list = [r[x:x+6] for x in xrange(0, len(r), 6)]
        except Exception, e:
            addon.log('**** Scrape Base Url Error occured: %s' %e)
            raise      
        return base_page_list

def scrape_media_url(page_url):
        # return a list of media urls for each title page_url
        try:


            resp = net.http_GET(page_url)
            html = resp.content
            media_url_list = []
            count = 0
            firedrive_count = 0
            allmyvideo_count = 0
            played_count = 0
            vodlocker_count = 0
            nowvideo_count = 0
            match = re.compile('<a href="(.+?)" target="_blank" rel="nofollow">\s*<img src=".+?" alt="" /> (.+?)\s*<!-- -->\s*</td>\s*<td><img src="http://www.iwatchonline.to/assets/images/English.gif"/ rel="tooltip" data-original-title="English"></td>\s*<td>(.+?)</td>\s*<td>(.+?)</td>').findall(html)
            if match:
                    
                    for media_url, host_server, time, quality in match:
                            #
                            
                            if host_server == 'Allmyvideos.net':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                    
                                            
                                            if allmyvideo_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    allmyvideo_count = 1
                            
                            if host_server == 'Firedrive.com':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                    
                                            
                                            if firedrive_count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    firedrive_count = 1                                  

                            if host_server == 'Sockshare.com':
                                    
                                    if quality == 'HD' or quality == 'DVD':
                                            
                                            if count == 0:
                                                    resp = net.http_GET(media_url)
                                                    html = resp.content
                                                    r = re.findall(r'<div class="row-fluid">\s*<iframe name="frame" class="frame" src="(.+?)"',html)
                                                    media_url = r[0]
                                                    media_url_list.append(media_url)
                                                    count = 1
                                    
            else:
                    addon.log('unable to find a media url for the page url %s' % page_url)        
            
        except Exception, e:
            addon.log('**** Scrape Media URL from given Page URL Error occured: %s' % e)
            raise      
        return media_url_list

def ovhd_film(url):

    try:

        resp = net.http_GET(url)
        html = resp.content
        clean_html = myutils.clean(html)

        match = re.compile(r'<(.+?)><title>(.+?)</title><link>(.+?)</link><thumbnail>(.*?)</thumbnail><fanart>(.*?)</fanart><.+?>').findall(clean_html)

        totalitems = len(match)

        for flavour, title, link, thumbnail, fanart in match:
            if link == 'search':

                # return thumb, backdrop and name for stream display
                addon.add_directory({'mode' : '410' , 'url' : link, 'thumb' : thumbnail, 'backdrop' : fanart, 'name' : title, 'videoType' : 'Movie'}, {'title': title}, total_items=totalitems, img =  thumbnail, fanart = fanart)

 
      
    except Exception, e:
        addon.log('**** There was a rip.ovhd_film error: %s' %e)
        raise
    return

def ovhd_tv(url):

    try:

        resp = net.http_GET(url)
        html = resp.content
        clean_html = myutils.clean(html)

        match = re.compile(r'<(.+?)><title>(.+?)</title><link>(.+?)</link><thumbnail>(.*?)</thumbnail><fanart>(.*?)</fanart><.+?>').findall(clean_html)

        totalitems = len(match)

        for flavour, title, link, thumbnail, fanart in match:
            if link == 'search':

                # return thumb, backdrop and name for stream display
                addon.add_directory({'mode' : '510' , 'url' : link, 'thumb' : thumbnail, 'backdrop' : fanart, 'name' : title, 'videoType' : 'tvshow'}, {'title': title}, total_items=totalitems, img =  thumbnail, fanart = fanart)

 
      
    except Exception, e:
        addon.log('**** There was a rip.ovhd_tv error: %s' %e)
        raise
    return

def ovhd_list_film_streams(title, url, backdrop, thumb):
    base_url = 'http://www.iwatchonline.to/'
    search_url = 'http://www.iwatchonline.to/search'

    try:
        resp = net.http_GET(base_url)
        search_content = net.http_POST(search_url, { 'searchquery' : title, 'searchin' : 'm'} ).content.encode('utf-8')
        # get the href url for the title
        dirty_html = re.findall('(?s)<table(.+?)</table>', search_content)
        clean_html = myutils.clean(dirty_html[0])       
        match = re.compile('<img.+?src=\".+?\".+?<a.+?href=\"(.+?)\">.+?</a>').findall(clean_html)
        # make the streams for the title  
        for link in match:
            film_streams(title, link, backdrop, thumb)

    except Exception, e:
        addon.log('**** There was a film iwol error: %s' %e)

    return

def ovhd_tv_seasons(title, url, backdrop, thumb, imdbnum):
    # derive seasons from title only. URL argument not currently used.
    base_url = 'http://www.iwatchonline.to/'
    search_url = 'http://www.iwatchonline.to/search'
    if DEBUG == 'true':
        addon.log('--- title parsed to ovhd_tv_seasons is: %s' %title)

    try:
        resp = net.http_GET(base_url)
        # the returned html will have the url for the title
        html = net.http_POST(search_url, { 'searchquery' : title, 'searchin' : 't'} ).content.encode('utf-8')
        clean_html = myutils.clean(html)

        # on the rare occassion we can get multiple titles returned so we need to find the correct one
        match = re.compile(r'<tr>  <td><img src=".+?" alt=".*?"><a href="(.+?)".*?>(.+?)<\/a>  <\/td><\/tr>').findall(clean_html)

        if match:
            totalitems = len(match)
            # some debug info to explain the number of possible titles
            if DEBUG == 'true':
                addon.log('--- %s has %d possible matches that need to be resolved to one match' %(title, totalitems))

            if totalitems == 1:
                # one title, at match [0][1]
                title_url = match [0][0]
                
                if DEBUG == 'true':
                    addon.log('--- One title found %s has one media_url associated %s' %(title, title_url))
            if totalitems > 1:
                # multiple titles, need to get correct one
                for match_url, match_title in match:

                    if match_title == title:
                        title_url = match_url
                        if DEBUG == 'true':
                            addon.log('--- %s is now matched with %s' %(title, title_url))
                    else:
                        # debug to show title and no title_url match
                        if DEBUG == 'true':
                            addon.log('--- %s is not a match with the title %s being parsed' %(match_title, title))


        if title_url:
            # get the title url page and display seasons
            
            if DEBUG == 'true':
                addon.log('--- title_url in ovhd_tv_seasons is: %s' %title_url)
            resp = net.http_GET(title_url)
            html = resp.content
            clean_html = myutils.clean(html)
            match = re.compile(r'<a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#(.+?)">').findall(clean_html)
            totalitems = len(match)
            for season in match:
                # return thumb, backdrop and name for episode display
                display_title = season.capitalize()
                display_title = '[COLOR yellow]' + display_title[:6] + ' ' + display_title[6:] + '[/COLOR]'


                addon.add_directory({'mode' : '520' , 'url' : title_url, 'thumb' : thumb, 'backdrop' : backdrop, 'name' : season, 'videoType' : 'tvshow', 'dirmode' : season, 'imdbnum' : imdbnum}, {'title': display_title}, total_items=totalitems, img =  thumb, fanart = backdrop)     
            
        if not title_url:
            addon.log('--- Could not find a title_url in ovhd_tv_seasons for: %s' %title)

    except Exception, e:
        addon.log('**** ovhd_tv_seasons - Could not find tv season: %s' %e)

    return

def ovhd_tv_episodes(title, url, backdrop, thumb, imdbnum, dirmode):
    # derive episodes from url and title, that is, season.
    # for example if the title is season01 then all the episodes for season01
    # are displayed

    print title
    print url
    print imdbnum
    print dirmode

    meta_params = {'name':'None' , 'year':'None', 'category' : 'TV_SddEdd'}

    if DEBUG == 'true':
        addon.log('--- season parsed to ovhd_tv_episodes is: %s' %title)

    try:
        resp = net.http_GET(url)
        html = resp.content
        clean_html = myutils.clean(html)
        # first we get the correct season table
        match = re.compile(r'<div id="%s"(.+?)<\/tbody><\/table>' %title).findall(clean_html)

        if match:
            # now get the episodes from the season table
            season_table = match[0]
            if DEBUG == 'true':
                addon.log('--- iwol season_table in match is : %s' %season_table)
            
            match2 = re.compile(r'<a href="(.+?)"><i class=".+?"></i>(.+?)</a></td>  <td>(.+?)</td>').findall(season_table)
            totalitems = len(match)
            if match2:
                for url, episode, name in match2:

                    episode_name = '[COLOR aqua]' + episode + ' : ' + name + '[/COLOR]'

                    addon.add_directory({'mode' : '530' , 'url' : url, 'thumb' : thumb, 'backdrop' : backdrop, 'name' : episode_name, 'videoType' : 'tvshow'}, {'title': episode_name}, total_items=totalitems, img =  thumb, fanart = backdrop)
                
            if not match2:
                if DEBUG == 'true':
                    addon.log('--- iwol found no episode match for season_table : %s' %season_table)


        if not match:
            addon.log('--- iwol - no match for season table %s at url %s' %(title,url))

    except Exception, e:
        addon.log('**** ovhd_tv_episodes - Could not find tv episode: %s' %e)

    return

def ovhd_list_tv_streams(name, url, backdrop, thumb):

    tv_streams(name, url, backdrop, thumb)

    return

