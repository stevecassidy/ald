// make_aust_lex.cpp : Defines the entry point for the console application.
//

/* this program converts the australian learners dictionary into a format usable
	by htk as a lexicon of pronunciations

  JOHN DINES, QUT, 2001

  how its done:
	* first idientify the word to be pronouned is located on a line on its own and 
	is preceded by a '--' or a '[j31]\n[j11] after a 'WORD FAMILY' or similar
	* all the text between this and the next word pertains to this word, although there may
	be several pronunciations with in
	* pronunciations are enclosed by '/  /'
	* [j???] refers to non ascII symbols
	* \font,0\ sets the font
	* [cf1,2,3] are commands for regular, bold or italic font
	* [cp?.?] sets the text size
	* [hmp3] ??? don't know what this does
	* and lots lots more.....
*/

#include "stdafx.h"

// some global flags
bool is_symbol;
bool is_skipped;
bool flag;

EST_String tempBuf;

EST_String strbuf;
EST_Token tokbuf;

EST_StrStr_KVL phoneList;
EST_StrStr_KVL charMap;

static EST_String get_next_def(EST_TokenStream &tokStream);

static EST_Token filter_next_token(EST_TokenStream &tokStream);

static EST_String get_pronunciation(EST_TokenStream &tokStream, bool &is_found);

static EST_StrListList &process_pronunciation(EST_String &pronuniciation);

static EST_String get_next_phone(EST_TokenStream &tokStr);

static EST_String recurse_get_next_phone(EST_TokenStream &tokStr, EST_String phone);

static EST_String filter_word(EST_String &word);

int main(int argc, char* argv[])
{
	// parsing 
	if (argc != 4){
		perror("Usage make_aust_lex <input lexicon> <output lexicon> <flag>\n");
		printf("The flag indicates whether you wish to use multiple definitions\n");
		printf("When Decoding (1 for 'yes', 0 for 'no')\n");
		return 0;
	}

	flag = atoi(argv[3]);

	// open file for output
	FILE *fp_out;
	if (!(fp_out = fopen(argv[2],"w"))){
		perror("Can not open file for output\n");
		exit(EXIT_FAILURE);
	}

	// load the character map
	char key[100], val[100];
	FILE *fp_chmap;
	if (!(fp_chmap = fopen("char_map.txt","r"))){
		perror("Can not open character map \"char_map.txt\"\n");
		exit(EXIT_FAILURE);
	}
	while (!feof(fp_chmap)){
		fscanf(fp_chmap,"%s %s",key,val);
		charMap.add_item(key,val);
	}
	fclose(fp_chmap);

	// load the phone list and map
	FILE *fp_phonelist;
	if (!(fp_phonelist = fopen("phone_list.txt","r"))){
		perror("Can not open phone list \"phone_list.txt\"\n");
		exit(EXIT_FAILURE);
	}
	while (!feof(fp_phonelist)){
		fscanf(fp_phonelist,"%s %s",key, val);
		phoneList.add_item(key,val);
	}
	fclose(fp_phonelist);

	// the container classes for words and pronunications...
	EST_StrListList pronunList;
	EST_StrListList pronunWord;
	EST_String Word, Pronun;
	EST_Token tokWord;
	bool is_found;

	// define the input stream
	EST_TokenStream inputLex;
	EST_Token tok;
	EST_String def;
    inputLex.open(argv[1]);
	inputLex.set_WhiteSpaceChars(" \n+~");
	inputLex.set_SingleCharSymbols("/\\[]");

	// define the definition stream
	EST_TokenStream defStream;
	int line;
	
	tokbuf = ""; // this is a buffer containing the start of the next definition
	// obtained in order to determine the locaiton of the end of the previous definition
	def = get_next_def(inputLex); // find the start of the first definition
	while (!inputLex.eof()){
		// get the next definition from the text
    	def = get_next_def(inputLex);
		defStream.open_string(def);
		defStream.set_PunctuationSymbols(",");
		defStream.set_WhiteSpaceChars("- \n~");
	    defStream.set_SingleCharSymbols("/[]");
		
		// this gets the word from the definition
		while ((tokWord = defStream.get()).string().length() <= 0);
		Word = tokWord.string()+ tokWord.punctuation(); line = defStream.linenum();
		tokWord = defStream.peek();
		while (defStream.linenum() == line){
			tokWord = defStream.get();
			Word += tokWord.whitespace() + tokWord.string() + tokWord.punctuation();
			tokWord = defStream.peek();
		}
		Word = filter_word(Word);

		tempBuf = Word;

		// this gets the pronunciation from the definition
		defStream.set_WhiteSpaceChars(" \n");
		Pronun = get_pronunciation(defStream, is_found); // bordered by the '/ /' delimiters

		// some dictionary items don't include a pronunciation -- only process
		// those which do
		if (is_found){
			// this converts the pronunciation to the symbols used by ANDSOL and puts them in a strListList
			pronunWord = process_pronunciation(Pronun);

			// for each pronunciation in list append this to the list of all pronunications
			for (int i = 0; i < pronunWord.length(); i++){
				pronunWord.nth(i).prepend(Word);
				pronunList.append(pronunWord.nth(i));				
			}
		}
		defStream.close();
	}

	// now output the pronunciations (this could be done earlier up but it's neater to have
	// them all stored in the one container, especially if more processing is to be done
	// later on - eg to look for repeated pronunciations)
	for (int i = 0; i < pronunList.length(); i++){
		fprintf(fp_out,"%-20s",pronunList.nth(i).nth(0).str());
		for (int j = 1; j < pronunList.nth(i).length(); j++){
			if (pronunList.nth(i).nth(j) != "-") // remove any hyphens still present in the pronunciation
				fprintf(fp_out," %s",pronunList.nth(i).nth(j).str());
		}
		fprintf(fp_out,"\n");
	}

	return 0;
}

static EST_String get_next_def(EST_TokenStream &tokStream){
	EST_String def;
	EST_Token tok;
	bool end_def = false;

	if (tokbuf != "")
		def = tokbuf.string();
	while (!end_def){
		tok = filter_next_token(tokStream);
		
		// check to see if we're at the end of the definition
		if (tok.string().contains("j111") || tokStream.eof()){
			tokbuf = "";
			break;
		}
		if (tok.string().contains("--")){
			tokbuf = tok;
			break;
		}

		if (is_symbol)
			def += tok.whitespace() + "[" + tok.string() + "]";
		else if (is_skipped)
			def += strbuf + tok.string();
		else
			def += tok.whitespace() + tok.string();
				
	}

	return def;
};


static EST_Token filter_next_token(EST_TokenStream &tokStream){
	EST_Token tok;
	EST_String str;
	bool valid_tok = false;

	// need to filter out commands '\  \', some '[  ]' commands and lines preceded by '~'
	is_symbol = false;
	is_skipped = false;
	strbuf = EST_String("");
	while (!valid_tok){
		tok = tokStream.get();
						
		if (tok.string() == "~"){
			if (tok.whitespace() != ""){
				is_skipped = true;
				strbuf += tok.whitespace();
			}

			tokStream.get_upto_eoln();
			valid_tok = false;
				
		}else if (tok.string() == "["){
			if (tok.whitespace() != ""){
				is_skipped = true;
				strbuf += tok.whitespace();
			}

			tok = tokStream.peek();
			if (!tok.string().matches(EST_Regex("^[ocmjhi]\\([!-z]\\)*"))){
				tok = tokStream.get();
				if (tok.string() == "ap"){  // this is the header command nothing on this line is of interest
					tokStream.get_upto_eoln();
					valid_tok = false;
				}else{ // this command does not have a closing ']' but is only two characters
					tokStream.seek(tokStream.tell()-tok.string().length()+1);
					valid_tok = false;
				}
					
			}else{  // or get up until the next close bracket
				tok = tokStream.get_upto("]");
				if (tok.string().str()[0]=='j'){
					valid_tok = true;
					is_symbol = true;
				}else{
					valid_tok = false;
				}
			}

		}else if (tok.string() == "\\"){
			if (tok.whitespace() != ""){
				is_skipped = true;
				strbuf += tok.whitespace();
			}

			tok = tokStream.get_upto("\\");
			valid_tok = false;

		}else{
			valid_tok = true;
		} 
	}
	
	return tok;
}

static EST_String get_pronunciation(EST_TokenStream &tokStream, bool &is_found){
	EST_String pronun;
	EST_Token tok;

	for (;;){
		tok = filter_next_token(tokStream);

		if (tok.string() == "/"){
			tok = tokStream.get_upto("/");
			is_found = true;
			break;
		}
		
		if (tokStream.eof()){
			is_found = false;
			break;
		}
		
	}

	return tok.string();
};

/* what needs to be considered for this function 
	- mapping the characters to the ANDOSL set
	- generating multiple pronunciations
	- generaing pronunciations from only partial pronunciations
*/

static EST_StrListList &process_pronunciation(EST_String &pronunciation){
	EST_StrList phoneList;
	EST_StrListList *pronunList = new EST_StrListList;
	EST_String phone;

	// first identify process the first pronunciation (as there may be more than one)
	EST_TokenStream tokStr;
	EST_Token tok;

	tokStr.open_string(pronunciation);
	tokStr.set_WhiteSpaceChars(" |\n");
	tokStr.set_SingleCharSymbols("[]-,pbtkgfvszmnNlrjwhieado");

	//convert the token string to the symbols that we need
	EST_String newPronun(""), newPhone;
	while (!tokStr.eof()){
		tok = filter_next_token(tokStr);
		if (is_symbol)
			newPhone = EST_String("[") + tok.string() + "]";
		else
			newPhone = tok.string();
		newPronun += charMap.val(newPhone) + " ";
		if (!charMap.present(newPhone)){ // good for debugging
			cerr << "symbol: " << newPhone << " not present in character map" << endl;
			getchar();
		}

	}

	tokStr.open_string(newPronun);
	tokStr.set_WhiteSpaceChars(" ");
	tokStr.set_SingleCharSymbols(",';-");

	while ((tokStr.peek()).string() != "," && !(tokStr.eof())){
		phone = get_next_phone(tokStr);
		phoneList.append(phone);
	}

	pronunList->append(phoneList);

	if (flag){
	// now look for alternative pronunciations and process them accordingly
	// these second pronunciations may or may not be whole 
	// (ie I may need to use part of the first pronunciation -- look for the '-'
	while (!(tokStr.eof())){
		phoneList.clear();
		
		phone = get_next_phone(tokStr);
		while ((tokStr.peek()).string() != "," && !(tokStr.eof())){
			phone = get_next_phone(tokStr);
			phoneList.append(phone);
		}

		// are these only partial pronunciations
		if (phoneList.nth(phoneList.length()-1).matches("-")){ // append to the start
			char chget;
			int move = 0;
			bool is_exit = false;
			
			cout <<endl << "==========" << endl;
			cout << "Word: " << tempBuf << endl;
			cout << "Pronunciation #1: " << pronunList->nth(0) << endl;
			cout << "Compound Pronunciation: " << phoneList << endl << endl;;
			cout << " Move Join [+-] or press 'a' to accept " << endl; cout.flush();

			phoneList.remove_nth(phoneList.length()-1);
			while (!is_exit){
				
				for (int i = 0; i >= 0 && i < phoneList.length()+move && i < phoneList.length(); i++)
					cout << phoneList.nth(i) << " " ;
				cout << " || ";
				for (int i = phoneList.length()+move; i >= 0 && i < pronunList->nth(0).length(); i++)
					cout << pronunList->nth(0).nth(i) << " ";
				cout.flush();

				chget = _getch();

				cout << "                " ;
				for (i = 0; i < pronunList->nth(0).length()*4+16; i++)
					cout << "\b";
				
				switch (chget){
					case '+':
						{
							if (move < pronunList->nth(0).length()-phoneList.length())
								move++;
							break;
						} 
					case '-':
						{
							if (-move < phoneList.length())
								move--;
							break;
						} 
					case 'a':
						{
							is_exit = true;
							break;
						}
					default:
						{
							//cerr << "Press '+' '-' or the <enter> key" << endl;
						}
				}

			}

			if (move <= 0){
				for (int i = 0; i < -move; i++)
					phoneList.remove_nth(phoneList.length()-1);
				for (int i = phoneList.length(); i < pronunList->nth(0).length(); i++)
					phoneList.append(pronunList->nth(0).nth(i));
			}else{
				for (int i = phoneList.length()+move; i < pronunList->nth(0).length(); i++)
					phoneList.append(pronunList->nth(0).nth(i));
			}

			cout << endl;

			//cout << "output phone list: " << phoneList << endl;
			//getchar();

		}
		
		if (phoneList.nth(0).matches("-")){ // append to the end

						char chget;
			int move = 0;
			bool is_exit = false;
			
			cout <<endl << "==========" << endl;
			cout << "Word: " << tempBuf << endl;
			cout << "Pronunciation #1: " << pronunList->nth(0) << endl;
			cout << "Compound Pronunciation: " << phoneList << endl << endl;;
			cout << " Move Join [+-] or press 'a' to accept " << endl; cout.flush();

			phoneList.remove_nth(0);
			while (!is_exit){
				for (int i = 0; i >= 0 && i < pronunList->nth(0).length() && i < pronunList->nth(0).length()-phoneList.length()+move; i++)
					cout << pronunList->nth(0).nth(i) << " ";
				cout << " || ";
				for (int i = 0+(move)*(move>0); i < phoneList.length(); i++)
					cout << phoneList.nth(i) << " " ;
				cout.flush();
				
				chget = _getch();

				cout << "                ";
				for (i = 0; i < pronunList->nth(0).length()*4+16; i++)
					cout << "\b";
				
				switch (chget){
					case '+':
						{
							if (move < phoneList.length())
								move++;
							break;
						} 
					case '-':
						{
							if (-move < pronunList->nth(0).length()-phoneList.length())
								move--;
							break;
						} 
					case 'a':
						{
							is_exit = true;
							break;
						}
					default:
						{
							//cerr << "Press '+' '-' or the <enter> key" << endl;
						}
				}
			}

			if (move >= 0){
				for (int i = 0; i < move; i++)
					phoneList.remove_nth(0);
				for (int i = pronunList->nth(0).length() - phoneList.length()-1; i >= 0; i--)
					phoneList.prepend(pronunList->nth(0).nth(i));
			}else{
				for (int i = pronunList->nth(0).length() - phoneList.length()-1+move; i >= 0; i--)
					phoneList.prepend(pronunList->nth(0).nth(i));
			}

			cout << endl;

			//cout << "output phone list: " << phoneList << endl;
			//getchar();
		}

		pronunList->append(phoneList);
	}
	}

	return *pronunList;
};

static EST_String get_next_phone(EST_TokenStream &tokStr){
	EST_Token tok;
	EST_String phone;
	bool primary_stress = false;
	bool secondary_stress = false;

	phone = tokStr.get().string();

	if (phone == "`"){
		primary_stress = true;
		phone = tokStr.get().string();  //now get the phone to be "stressed"
	}else if (phone == ";"){
		secondary_stress = true;
		phone = tokStr.get().string();
	}

	if (phone.matches(EST_Regex("^[t]+"))){ // check for affricates
		tok = tokStr.peek();
		if (tok.string().matches(EST_Regex("^[S]+"))){
			phone += tokStr.get().string();
		}
	}else if (phone.matches(EST_Regex("^[d]+"))){
		tok = tokStr.peek();
		if (tok.string().matches(EST_Regex("^[Z]+"))){
			phone += tokStr.get().string();
		}
	}else{
		// now check to see if this phone comprises of multiple entries 
		// -- recursive approach is best?
		phone = recurse_get_next_phone(tokStr, phone);
	}

	if (!phoneList.present(phone)){
		cerr << "phone: " << phone << " not present in phone list file" << endl;
		getchar();
	}
	phone = phoneList.val(phone);

	if (primary_stress)
		phone += "1";
	else if (secondary_stress)
		phone += "2";

	return phone;
};

static int num_matches(EST_String phone);

static EST_String recurse_get_next_phone(EST_TokenStream &tokStr, EST_String phone){
	EST_Token tok;
	EST_String temp;
	int count;

	count = num_matches(phone);

	if (count > 1){
		tok = tokStr.peek();
		if (tok.string().length() > 0){
			temp = phone + tok.string();
			count = num_matches(temp);
			if (count >= 1){
				tokStr.get();
				phone = temp;
				if (count == 1)
					return phone;
				else
					return recurse_get_next_phone(tokStr, phone);
			}
		}
	}

	return phone;
}

static int num_matches(EST_String phone){
	int count = 0;
	phone = EST_String("^") + phone + "\\([@:a-zA-Z]\\)*";
	EST_Regex expr(phone);
	
	EST_UItem *kvlItem;
	for (kvlItem = phoneList.head(); kvlItem != 0; kvlItem = next(kvlItem)){
		if (phoneList.key(kvlItem).matches(expr))
			count++;
	}

	return count;
}

static EST_String filter_word(EST_String &word){

	EST_TokenStream tokStr;
	EST_Token tok;

	tokStr.open_string(word);
	tokStr.set_WhiteSpaceChars(" ");
	tokStr.set_SingleCharSymbols(",");

	word = tokStr.get();
	while (!tokStr.eof() && tokStr.peek().string() != ","){
		word += EST_String("-") + tokStr.get();	// hyphenate compound dictionary items
	}

	return downcase(word);
}
