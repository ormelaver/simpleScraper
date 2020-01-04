import requests
from bs4 import BeautifulSoup
import lxml
import re
import concurrent.futures
MAX_THREADS = 4

#a function that cleans all unwanted chars
def cleanText(text):
    if '\xa0' in text: #handle get_text's bug with nbsp
        text = text.replace('\xa0', '').replace(' ', '')
    paranRemoved = re.sub(r'\([^)]*\)', '', text)
    bracketsRemoved =  re.sub(r'\[[^)]*\]', '', paranRemoved)
    if 'Also see' in bracketsRemoved:
        result = bracketsRemoved.split('Also')[0] #can also be done with text.find('a')
    else:
        result = bracketsRemoved
    return result

#a function that handles the special case of an empty string as collateral
#if the coll is of the form 'x see y' - attach them. otherwise, attach it to the coll '?'
def fixEmptyColl(data, key): 
    for name in key:
        newName = name.split('-')[0].replace('-', '')
        if '- See' in name:
            alreadyExists = name.split('See')[1].lstrip(' ')
            for animal in data:
                for coll in data[animal]:
                    if coll == alreadyExists:
                        data[animal].append(newName)
        else:
            data['?'].append(newName)
    try:
        data.pop('', None)
    except:
        print('key does not exist')
    return data


def arrangeList(animals):
    parsedDict = dict()
    for animal in animals:
        if not animal.find('td'): # remove A,B,C...Z rows
            animal.decompose()
            continue
        
        name = animal.select('tr td:nth-of-type(1)')[0]
        if name:
            name = name.get_text().rstrip()
        if (len(animal.find_all('td')) > 1): #handle the special case of "X-ray tetra"
            collaterals = animal.select('tr td:nth-of-type(6)')[0]
            if (collaterals.find('br')): #remove br tags and insert a whitespace instead to avoid collaterals from joining and creating an invalid collateral
                for coll in collaterals.find_all('br'):
                    coll.replace_with(' ')

            collateral = collaterals.get_text().rstrip()
        else:
            collateral = '?'
        cleanCol = cleanText(collateral)
        cleanName = cleanText(name)
        if (not(cleanCol in parsedDict)):
            colLength = len(cleanCol.split())
            if (colLength > 1): #if there is more than one collateral, split and insert
                splittedCol = cleanCol.split() 
                for coll in splittedCol:
                    if (not(coll in parsedDict)): 
                        parsedDict[coll] = [cleanName.strip()]
                    else:
                        parsedDict[coll].append(cleanName.strip())
            else:
                parsedDict[cleanCol] = [cleanName.strip()]
                 
        else:
            parsedDict[cleanCol].append(cleanName.strip()) 
    print(fixEmptyColl(parsedDict, parsedDict['']))

def parseHtml(page):
    soup = BeautifulSoup(page.content, 'lxml')
    table = soup.find_all('table')[2]
    return table.find_all('tr')[2:]
    

def init():
    try:
        page = requests.get('https://en.wikipedia.org/wiki/List_of_animal_names', timeout=5)
    except requests.ConnectionError as e:
        print("connection error.")
        print(str(e))
    except requests.Timeout as e:
        print("request timed out!")
        print(str(e))
    except requests.RequestException as e:
        print("General Error occured.")
        print(str(e))
    except KeyboardInterrupt:
        print("Someone closed the program.")
    if page.status_code != 200:
        print('The website is unreachable')
        return False
    animals = parseHtml(page)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor: #since we are not dealing with I/O and our input is only one page, the usage of threads is redundant.
        executor.map(arrangeList(animals), range(MAX_THREADS))                       #just wanted to show that I can handle it :)
    
if __name__ == "__main__":
    init()