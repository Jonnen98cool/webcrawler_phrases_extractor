import requests
from bs4 import BeautifulSoup



TO_SCRAPE = "https://cry-of-fear.fandom.com/wiki/FAMAS"
INCLUDE_TAGS = ["p", "big", "span"] #TODO: manually add more "text" elements to analyze here



def scrape_site(URL:str):
    res = requests.get(URL)
    #print(res.text)     #This is the entire HTTP response with all HTML
    soup = BeautifulSoup(res.text, "html.parser")   #Soup object

    site_contents = []   #2D list containing lists of the text contents of the various HTML elements such as <p>, <span> etc
    for i, tag in enumerate(INCLUDE_TAGS):
        site_contents.append(soup.find_all(tag))
        for j, element in enumerate(site_contents[i]):
            #print(f"Tag {tag}, Element {j}: {element.text}\n\n")
            pass
    

    return tag_contents



def to_wordlist(site_content, phrase_length:int, delimiter:str=' ') -> str:
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

        print(f"DEBUG: current wordlist: {wordlist}")

    return "\n".join(wordlist)



if __name__=="__main__":
    #phrases = scrape_site(TO_SCRAPE)
    #single_words = to_wordlist(phrases, 1, ' ')

    testing_list = [["One", "word", "phrases"], ["Now we're", "starting two", "word phrases"], ["Three word phrases", "are now incoming", "so brace yourself!"], ["11 12 13 14", "21 22 23 24", "31 32 33 34"]]
    single_words = to_wordlist(testing_list, 1, ' ')
    print(f"\nDEBUG: starting doulbe words now\n")
    double_words = to_wordlist(testing_list, 2, ' ')
    print(f"\nDEBUG: starting TRIPLE words now\n")
    tripple_words = to_wordlist(testing_list, 3, ' ')


    # Write to file
    try:
        final_wordlist = open("wordlist.txt", "w")
    except Exception as e:
        print(f"ERROR: could not open file for writing, exception:\n{e}")
    else:
        final_wordlist.write(single_words)
        final_wordlist.close()
