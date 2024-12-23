import requests
from bs4 import BeautifulSoup, SoupStrainer


#NOTE: Without a simple rule list (in this case stripping all dots), the phrase "Sony Ericsson W610i" does not get cracked. It's found on the page but it has a dot at the end.


#TODO: Still there are newlines making their way into the final wordlists. eleiminate.



TO_SCRAPE = "https://cry-of-fear.fandom.com/wiki/FAMAS"
INCLUDE_TAGS = ["p", "big", "small","span", "b", "strong", "i", "em", "mark", "del", "ins", "sub", "sup", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "q", "code", "li", "dt", "dd"] #TODO: manually add more "text" elements to analyze here
STRIP_CHARS = ["\n", "\r", "\t"]
IN_SCOPE = "https://cry-of-fear.fandom.com/wiki/"

DISALLOWED_FILE_EXTENSIONS = [".wav", ".ogg"] #TODO: I want to make a whitelist instead, but then how would I allow no file extension? Instead, this solution requires user to manually modify the blacklist.
LINK_NR = 0
STOP_AFTER_X_LINKS = 300
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



#Given a URL, gather all href's from it and visit each URL if it hasn't already been visited
#TODO: It visits .ogg and similar files, I don't want this
def build_sitemap(URL:str, link_nr:int):
    global LINK_NR
    if(LINK_NR >= STOP_AFTER_X_LINKS):    #TODO: temporary
        return
        
    print(f"\tINFO: processing link {link_nr}, URL = {URL}")
    skip_link = False
    res = requests.get(URL)
    links_on_url = []
    for link in BeautifulSoup(res.text, 'html.parser').find_all("a"):
        if link.has_attr('href'):
            if(link["href"].startswith(IN_SCOPE)):  #Will miss all links which are relative (and probably more), eg. /wiki/FAMAS
                for extension in DISALLOWED_FILE_EXTENSIONS: #Filter out URL's with disallowed file extensions
                    if(link["href"].endswith(extension)):
                        skip_link = True
                        break
                if(not skip_link):  
                    if(link["href"] not in SITE_LINKS): #If not already visited, visit link and extract recursively
                        SITE_LINKS.append(link['href'])
                        #global LINK_NR
                        LINK_NR += 1
                        build_sitemap(link["href"], LINK_NR)

    #links_string = "\n".join(links_on_url)
    #print(f"DEBUG: links: {links_string}")
    #return links_string




#TODO: Time measruement for how long it takes to extract all links
if __name__=="__main__":
    #Enumerate the website structure/sitemap
    root_URL = "https://cry-of-fear.fandom.com/wiki/Cry_of_Fear_Wiki"
    build_sitemap(root_URL, LINK_NR)
    site_links_string = "\n".join(SITE_LINKS)
    #print(f"\nDEBUG: Website complete sitemap:\n\n{site_links_string}")

    #Build the lists which will contain all words/phrases
    delimiter = " "
    words1 = []
    words2 = []
    words3 = []
    words4 = []
    for i, link in enumerate(SITE_LINKS):
        print(f"INFO: Extracting from link nr {i}: \"{link}\":")
        if(i <= 1000):
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
        


#    testing_list = [["One", "word", "phrases"], ["Now we're", "starting two", "word phrases"], ["Three word phrases", "are now incoming", "so brace yourself!"], ["11 12 13 14", "21 22 23 24", "31 32 33 34"]]
#    single_words = to_wordlist(testing_list, 1, ' ')
#    print(f"\nDEBUG: starting doulbe words now\n")
#    double_words = to_wordlist(testing_list, 2, ' ')
#    print(f"\nDEBUG: starting TRIPLE words now\n")
#    tripple_words = to_wordlist(testing_list, 3, ' ')


