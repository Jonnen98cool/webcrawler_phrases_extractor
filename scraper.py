import requests
import time
from bs4 import BeautifulSoup, SoupStrainer


#NOTE for challenge "Can't Weld When Gas Are Gone": Without a simple rule list (in this case stripping all dots), the phrase "Sony Ericsson W610i" does not get cracked. It's found on the page but it has a dot at the end.


#TODO: Still there are newlines or something making their way into the final wordlists. eleiminate.
#   - in the 3-word file for example, Ctrl + f :ing for "Iglesias" reveals the problem (this is because certain words in the phrase are enclosed in <b> tags?)
#TODO: Multithreading, I think I'm network-bottlenecked?


#NOTE: These few variables you need to manually edit for each site.
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
START_URL = "https://cry-of-fear.fandom.com/wiki/Cry_of_Fear_Wiki" #NOTE: the URL you want the scraper to start from.
ROOT_URL = "https://cry-of-fear.fandom.com/"   #NOTE: this is the webroot, so all relative paths go from this. An example of a relative path is:   href="/wiki/Co-op_Campaign"
IN_SCOPE = "https://cry-of-fear.fandom.com/wiki"      #NOTE: Sometimes appropriately set to the same URL as the webroot, all found URL:s must start with this string in order to be included for processing (or translate to starting with this in the case of relative paths being used).
OUT_OF_SCOPE_PATH = ["/Special:Log", "/Special:Search", "/register", "/login", "/reset-password", "/signin", "/User", "/File:", "/Template:", "/Forum:", "/Talk:", "/Message_Wall:", "/Special:", "/Thread:", "/MediaWiki:"] #NOTE: This list is relative to the IN_SCOPE value and needs to be custom-edited for each site. If any of these values directly follow the IN_SCOPE URL, don't process that URL. 
OUT_OF_SCOPE_STRING = ["?", "#"] #NOTE: if any of the substrings in here are detected ANYWHERE as part of the URL AFTER the IN_SCOPE, don't process that URL.
DISALLOWED_FILE_EXTENSIONS = [".wav", ".ogg", ".png", ".jpg", ".jpeg", ".webp", ".mp3", ".mp4"] #NOTE: Don't process any path's ending with these strings.
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


INCLUDE_TAGS = ["p", "big", "small","span", "b", "strong", "i", "em", "mark", "del", "ins", "sub", "sup", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "q", "code", "li", "dt", "dd"] #TODO: manually add more "text" elements to analyze here. Are there any more??
STRIP_CHARS = ["\n", "\r", "\t"]    #NOTE: strip all occurences of these chars in gathered phrases.


LINK_NR = 0
#STOP_AFTER_X_LINKS = 3000
SITE_LINKS = [] #Dynamically filled with all links/pages on the site





def scrape_site(URL:str):
    res = requests.get(URL)
    #print(res.text)     #This is the entire HTTP response with all HTML
    soup = BeautifulSoup(res.text, "html.parser")   #Soup object

    site_contents = []   #2D list containing lists of the text contents of the various HTML elements such as <p>, <span> etc
    for i, tag in enumerate(INCLUDE_TAGS):
        tag_contents = []
        for j, element in enumerate(soup.find_all(tag)):
            stripped_string = element.text  # Get the text from the HTML tag (similar to innerHTML)
            for c in STRIP_CHARS:           #Strip unwanted characters from the string
                stripped_string = stripped_string.replace(c, "")
            tag_contents.append(stripped_string)
        site_contents.append(tag_contents)


    return site_contents



def to_wordlist(site_content, phrase_length:int, delimiter:str=' ') -> [str]:
    wordlist = []
    for tag_content in site_content:
        for phrase in tag_content:
            nr_of_words = phrase.count(delimiter) + 1   #I can see this NOT being a robust way of achieving what I wan
            delimiter_indexes = [index for index, char in enumerate(phrase) if(char == delimiter)]
            word_separator_indexes = [0] + delimiter_indexes + [len(phrase) - 1]    #Add index 0 and final index

            if(nr_of_words >= phrase_length):
                for i in range(nr_of_words - phrase_length + 1):
                    if(i == 0 and nr_of_words == phrase_length): 
                        wordlist.append(phrase[word_separator_indexes[i] + 0 : word_separator_indexes[i+phrase_length] + 1])
                    elif(i == 0 and nr_of_words != phrase_length):
                        wordlist.append(phrase[word_separator_indexes[i] + 0 : word_separator_indexes[i+phrase_length] + 0])
                    elif(i == nr_of_words - phrase_length):
                        wordlist.append(phrase[word_separator_indexes[i] + 1 : word_separator_indexes[i+phrase_length] + 1])
                    else:
                        wordlist.append(phrase[word_separator_indexes[i] + 1 : word_separator_indexes[i+phrase_length] + 0])

        #print(f"DEBUG: current wordlist: {wordlist}")
    wordlist = list(set(wordlist))
    #return "\n".join(wordlist)
    return wordlist



def write_wordlist(name:str, content:str):
    # Write to file
    try:
        wordlist = open(name, "w")
    except Exception as e:
        print(f"ERROR: could not open file for writing, exception:\n{e}")
    else:
        wordlist.write(content)
        wordlist.close()
        print(f"INFO: wrote contents to \"{name}\"")



#Given a URL, gather all href's from it and visit each URL if it hasn't already been visited. Recursive.
#NOTE: one commented-out href on CoF wiki start page literally looks like this:   href="//cry-of-fear.fandom.com"  (that means it's not a bug in your program)
def build_sitemap(URL:str, link_nr:int):
    global LINK_NR
#    if(LINK_NR >= STOP_AFTER_X_LINKS):    #temporary
#        return
        
    res = requests.get(URL)
    links_on_url = []
    #print(f"\tINFO: processing link {link_nr}, code = {res.status_code}, URL = {URL}\t\tCL = {len(res.content)}")
    print(f"\tINFO: processing link {link_nr}, code = {res.status_code}, URL = {URL}")

    if(res.status_code == 404): #NOTE: will miss any important links on 404 sites.
        return

    for link in BeautifulSoup(res.text, 'html.parser').find_all("a"):   #TODO: can links be found in other HTML tags than <a> ?
        exit_iteration = False
        if(link.has_attr('href')):
            link_text = link["href"]  

            #If relative path is being used, construct an absolute path from it called "to_visit"
            to_visit = None
            if(link_text.startswith("/")):    #Handle relative links.
                to_visit = ROOT_URL[:-1] + link_text if(ROOT_URL.endswith("/")) else ROOT_URL + link_text   #domain + the relative link. This assumes a relative URL always start with /
            else: to_visit = link_text

            #Check if we are in scope
            if(not to_visit.startswith(IN_SCOPE)):
                exit_iteration = True

            if(not exit_iteration):
                #Check if substring occuring anywhere in the path is blacklisted (only checks the part after the IN_SCOPE)
                scope_length = len(IN_SCOPE)
                for bad in OUT_OF_SCOPE_STRING:
                    if(bad in to_visit[scope_length:]):
                        exit_iteration = True
                        break

                if(not exit_iteration):
                    #Check if initial part of path is blacklisted
                    for bad in OUT_OF_SCOPE_PATH:
                        if(to_visit.startswith(IN_SCOPE + bad)):
                            exit_iteration = True
                            break

                    if(not exit_iteration):
                        #Check for blacklisted extensions
                        for extension in DISALLOWED_FILE_EXTENSIONS:
                            if(link_text.endswith(extension)):
                                exit_iteration = True
                                break


                        if(not exit_iteration):
                            #If we pass all checks and site has not already been visited, visit it
                            if(to_visit not in SITE_LINKS):
                                SITE_LINKS.append(to_visit)
                                LINK_NR += 1
                                build_sitemap(to_visit, LINK_NR)




if __name__=="__main__":
    #Enumerate the website structure/sitemap
    start_scrape = time.time()
    build_sitemap(START_URL, LINK_NR)
    site_links_string = "\n".join(SITE_LINKS)
    #print(f"\nDEBUG: Website complete sitemap:\n\n{site_links_string}")
    end_scrape = time.time()
    print(f"INFO: scraping finished in {end_scrape - start_scrape}s\n")

    #Build the lists which will contain all words/phrases
    start_wordlist_construction = time.time()
    delimiter = " "
    words1 = []
    words2 = []
    words3 = []
    words4 = []
    for i, link in enumerate(SITE_LINKS):
        print(f"\tINFO: Extracting phrases from link nr {i}: \"{link}\":")
        link_contents = scrape_site(link)
        words1 += (to_wordlist(link_contents, 1, delimiter))
        words2 += (to_wordlist(link_contents, 2, delimiter))
        words3 += (to_wordlist(link_contents, 3, delimiter))
        words4 += (to_wordlist(link_contents, 4, delimiter))
        
        #print(f"DEBUG: here is what's returned from scrape_site(): \n\n{link_contents}")

    #Remove duplicates
    words1 = list(set(words1))
    words2 = list(set(words2))
    words3 = list(set(words3))
    words4 = list(set(words4))

    #Write the lists to files
    write_wordlist("1_words.txt", "\n".join(words1))
    write_wordlist("2_words.txt", "\n".join(words2))
    write_wordlist("3_words.txt", "\n".join(words3))
    write_wordlist("4_words.txt", "\n".join(words4))

    end_wordlist_construction = time.time()
    print(f"INFO: wordlist generation finished in {end_wordlist_construction - start_wordlist_construction}s")
