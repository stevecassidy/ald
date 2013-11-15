
from nltk.tokenize import RegexpTokenizer





def tokenize_text(text):
    """Return a list of tokens from this text"""
    
    
    tokenizer = RegexpTokenizer(r"\\(\w|,)+|--|\w+|\[[a-z0-9.]+\]|[/()]")

    return tokenizer.tokenize(text)

def next_def(tokens):
    """An iterator over definitions in this token stream.
    Yields the next definition block as a sequence of tokens"""
    
    defblock = []
    for tok in tokens:
        if starts_definition(tok):
            if defblock != []:
                result = defblock
                defblock = []
                yield result
                
        defblock.append(tok)
    
def starts_definition(token):
    """Return true if this token can start a definition"""
    
    return token in ['--', '[j111]']


def process_definition(tokens):
    """Given a definition, return the headword and the pronunciation"""
    
    if not starts_definition(tokens[0]):
        return []
    
    headword = []
    pron = []
    in_pron = False
    done_hw = False
    for tok in tokens[1:]:
        if tok == '/':
            done_hw = True
            in_pron = not in_pron
            pron.append(tok)
        elif not done_hw:
            headword.append(tok)
        elif in_pron:
            pron.append(tok)
    
    return (headword, pron)
    
    

if __name__=='__main__':
    
    import sys
    textfile = sys.argv[1]
    h = open(textfile)
    text = h.read()
    h.close()
    
    tokens = tokenize_text(text)
    
    for defn in next_def(tokens):
        d = process_definition(defn)
        print d
        