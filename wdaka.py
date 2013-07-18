import Levenshtein
import json
import guess_language
from collections import defaultdict
import operator
import pywikibot
import re

print "opening largefile"
file = open('hasAKALC_shrink_lev65.json', 'r')
has = json.load(file)
print "opened largefile"

print "logging in"
en_wikipedia = pywikibot.Site('en', 'wikipedia')
wikidata = en_wikipedia.data_repository()
if not wikidata.logged_in(): wikidata.login()

propertyMap = {'LCCN': 'P244',
             'VIAF':'P214',
             'sex': 'P21',
             'imported from':'P143'}

#the current gerenator returns type Page, and we need ItemPage
def ItemPageGenerator(gen):
 for page in gen:
     yield pywikibot.ItemPage(page.site.data_repository(), page.title())

viaf_property_page = pywikibot.ItemPage(wikidata, 'Property:' + propertyMap['VIAF'])
pages_with_viaf = viaf_property_page.getReferences(total=100000000)
pages_with_viaf = ItemPageGenerator(pages_with_viaf)

wikipedias = {       "af": "q766705",       "als": "q1211233",       "an": "q1147071",       "ar": "q199700",       "arz": "q2374285",       "az": "q58251",       "ba": "q58209",       "be": "q877583",       "bg": "q11913",       "bn": "q427715",       "ca": "q199693",       "ceb": "q837615",       "ckb": "q4115463",       "cs": "q191168",       "cv": "q58215",       "cy": "q848525",       "da": "q181163",       "de": "q48183",       "diq": "q38288",       "dsb": "q8561147",       "el": "q11918",       "en": "q328",       "eo": "q190551",       "es": "q8449",       "et": "q200060",       "eu": "q207260",       "fa": "q48952",       "fi": "q175482",       "fr": "q8447",       "ga": "q875631",       "gl": "q841208",       "he": "q199913",       "hi": "q722040",       "hr": "q203488",       "hsb": "q2402143",       "ht": "q1066461",       "hu": "q53464",       "hy": "q1975217",       "id": "q155214",       "it": "q11920",       "ja": "q177837",       "jv": "q3477935",       "kk": "q58172",       "kn": "q3181422",       "ko": "q17985",       "ks": "q8565447",       "ksh": "q3568041",       "la": "q12237",       "lt": "q202472",       "mk": "q842341",       "ml": "q874555",       "mn": "q2998037",       "mr": "q3486726",       "ms": "q845993",       "my": "q4614845",       "nap": "q1047851",       "nds-nl": "q1574617",       "new": "q1291627",       "nl": "q10000",       "no": "q191769",       "oc": "q595628",       "or": "q7102897",       "pa": "q1754193",       "pl": "q1551807",       "pt": "q11921",       "ro": "q199864",       "ru": "q206855",       "sa": "q2587255",       "sco": "q1444686",       "se": "q4115441",       "sh": "q58679",       "simple": "q200183",       "sk": "q192582",       "sl": "q14380",       "sq": "q208533",       "sr": "q200386",       "su": "q966609",       "sv": "q169514",       "sw": "q722243",       "szl": "q940309",       "ta": "q844491",       "te": "q848046",       "tg": "q2742472",       "th": "q565074",       "tl": "q877685",       "tr": "q58255",       "uk": "q199698",       "ur": "q1067878",       "uz": "q2081526",       "vi": "q200180",       "vo": "q714826",       "war": "q1648786",       "yi": "q1968379",       "zh": "q30239",       "zh-min-nan": "q3239456",       "zh-yue": "q1190962",       "zu": "q8075204"   }
wikipediaslist = [lang for lang in wikipedias.iterkeys()]
#cases of interest
try:
    casesJSON = open('cases.JSON')
    cases = json.load(casesJSON)
    casesJSON.close()
    
    
except IOError:
    cases = {"prevtouched":0}
    for lang in wikipediaslist:
        cases[lang] = {'newka': 0, 'newaka': 0, 'hadka': 0, 'hadaka': 0}

def savecases():
    casesJSON = open('cases.JSON', 'w')
    json.dump(cases, casesJSON, indent=4)
    casesJSON.close()

def makenameset(namestring):
    namelist = namestring.replace(';',' ').replace(',',' ').replace('.',' ').split(' ')
    namelist = filter(lambda x: x != '', namelist)
    namelist = [nameword.strip() for nameword in namelist]
    nameset = set(namelist)
    return nameset
    
def isfirstlast(ka, aka):
    '''tests if ka and aka are perfect rearranegments of each other'''
    kaset = makenameset(ka)
    akaset = makenameset(aka)
    if akaset == kaset:
        return True
    else:
        return False


touched = 0
for page in pages_with_viaf:
    touched += 1
    print touched
    if cases['prevtouched'] >= touched:
        continue
    try:
        page_parts = page.get()
        claims = page_parts['claims']
        labels = page_parts['labels']
        aliases = page_parts['aliases']
        print aliases
    except pywikibot.data.api.APIError as err:
        print err.code
        print err.info
        continue
    nyms = None
    for claim_list in page_parts['claims'].itervalues():
        for claim in claim_list:
            if claim.id == 'p214':
                viafid = claim.target
                try:
                    nyms = has[viafid]
                except KeyError:
                    print 'no aka from lc on ', viafid, 'wikidata number ', page.title
    if nyms:
        #begin  the  aka ritual
        ka = nyms['ka']
        akas = nyms['aka']
        aliaseschanged = False
        for aka in akas:
            lcrat = Levenshtein.ratio(ka, aka)
            if lcrat < .3: #determined from hitogram
                gl = guess_language.guessLanguage(aka)
                gl = unicode(gl)
                if gl == 'UNKNOWN':
                    continue
                if not gl in wikipediaslist:
                    print 'weirdo language: ', gl
                    continue
                else:
                    wdlabel = None
                    wdaliases = None
                    try:
                        wdlabel = labels[gl]
                        cases[gl]['hadka'] += 1
                    except KeyError:
                        pass
                    try:
                        wdaliases = aliases[gl]
                        cases[gl]['hadaka'] += len(wdaliases)
                    except KeyError:
                        pass
                    #apply the business logic
                    #is there a label in this language
                    if not wdlabel:
                        labels[gl] = aka
                        page.editLabels(labels,bot=True)
                        cases[gl]['newka'] += 1
                        print 'omg label'

                    #otherwise is our aka suffiently far from the label
                    #first we check for first last confustion
                    if isfirstlast(wdlabel, aka):
                        print 'last, firt confusion'
                        continue
                    #then we check for other similarity
                    wdlabelrat = Levenshtein.ratio(wdlabel, aka)
                    if wdlabelrat < .65:
                        #are  there aliases
                        if wdaliases:
                            highestwdaliasrat = 0
                            #is our aka all sufficiently distant from the alaiases
                            for wdalias in wdaliases:
                                wdaliasrat = Levenshtein.ratio(unicode(wdalias), unicode(aka))
                                if wdaliasrat > highestwdaliasrat:
                                    highestwdaliasrat = wdaliasrat
                            if highestwdaliasrat < .5:
                                aliases[gl].append(aka)
                                aliaseschanged = True
                                cases[gl]['newaka'] += 1
                                print 'omg alias'
                        else:
                            aliases[gl] = [aka]
                            aliaseschanged = True
                            cases[gl]['newaka'] += 1
                            print 'omg alias'
        if aliaseschanged:
            page.editAliases(aliases,bot=True)
    cases['prevtouched'] = touched
    savecases()