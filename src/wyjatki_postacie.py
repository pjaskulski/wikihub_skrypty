""" Słownik wyjątków dla postaci (okreslanie imion i nazwisk) """

WYJATKI = { 
            'Szturm de Sztrem Tadeusz': 
                {'imie':'Tadeusz', 'nazwisko': 'Szturm de Sztrem'},
            'Szemberg Teofil de Reichembac':
                {'imie':'Teofil', 'nazwisko':'Szemberg de Reichembac'},
            'Strem de Zygmunt Fryderyk':
                {'imie':'Zygmunt', 'imie2': 'Fryderyk', 'nazwisko':'de Strem'},
            'Samuel de Sacerdotibus Patavinus':
                {'imie':'Samuel', 'nazwisko':'de Sacerdotibus Patavinus'},
            'Rużycki de Rosenwerth Włodzimierz Józef':
                {'imie':'Włodzimierz', 'imie2': 'Józef', 'nazwisko':'Rużycki de Rosenwerth'},
            'Piotr Świętopełk z Zambrzecza i z Nieznanowic':
                {'imie':'Piotr', 'imie2': 'Świętopełk'},
            'O’Byrn de Lassy Tytus Jan':
                {'imie':'Tytus', 'imie2': 'Jan', 'nazwisko':'O’Byrn de Lassy'},
            'Mitzler de Kolof Wawrzyniec Krzysztof':
                {'imie':'Wawrzyniec', 'imie2': 'Krzysztof', 'nazwisko':'Mitzler de Kolof'},
            'Maria Kazimiera de la Grange d’Arquien':
                {'imie':'Maria', 'imie2': 'Kazimiera', 'nazwisko':'de la Grange', 'nazwisko2':'d’Arquien'},
            'Le Brun Piotr':
                {'imie':'Piotr', 'nazwisko':'Le Brun'},
            'Le Brun Andrzej':
                {'imie':'Andrzej', 'nazwisko':'Le Brun'},
            'Le Brun Aleksander Antoni':
                {'imie':'Aleksander', 'imie2': 'Antoni', 'nazwisko':'Le Brun'},
            'Konstanty Olgierdowicz':
                {'imie':'Konstanty', 'nazwisko':'Olgierdowicz'},
            'Kasprzycki Stefan de Castenedolo':
                {'imie':'Stefan', 'nazwisko':'Kasprzycki de Castenedolo'},
            'Karol Ferdynand Waza':
                {'imie':'Karol', 'imie2': 'Ferdynand', 'nazwisko':'Waza'},
            'Jerzy Wilhelm':
                {'imie':'Jerzy', 'imie2': 'Wilhelm'},
            'Jan de Bossis Polonus':
                {'imie':'Jan', 'nazwisko':'de Bossis Polonus'},
            'Jan Andrzej de Valentinis':
                {'imie':'Jan', 'imie2': 'Andrzej', 'nazwisko':'de Valentinis'},
            'Jan z Książąt Litewskich':
                {'imie':'Jan'},
            'Jan Jacobs van Asten':
                {'imie':'Jan', 'nazwisko':'Jacobs van Asten'},
            'Jan zw. Kropidło':
                {'imie':'Jan'},
            'Iwo Odrowąż':
                {'imie':'Iwo', 'nazwisko':'Odrowąż'},
            'Iwo Goły':
                {'imie':'Iwo'},
            'Herrenschwand de Greng Jan Fryderyk':
                {'imie':'Jan', 'imie2': 'Fryderyk', 'nazwisko':'Herrenschwand de Greng'},
            'Henryk zw. Kietliczem':
                {'imie':'Henryk'},
            'Henryk zw. Pincerna':
                {'imie':'Henryk'},
            'Henryk III Walezy':
                {'imie':'Henryk'},
            'Henryk I Brodaty': 
                {'imie':'Henryk'},
            'Henryk II Pobożny':
                {'imie':'Henryk'},
            'Henryk IV Probus': 
                {'imie':'Henryk'},
            'Henryk V Gruby':
                {'imie':'Henryk'}, 
            'Haye de la Karol':
                {'imie':'Karol', 'imie2': '', 'nazwisko':'de la Haye'},
            'Gordon de Huntlej Henryk':
                {'imie':'Henryk', 'imie2': '', 'nazwisko':'Gordon de Huntlej'},
            'Füger von Rechtborn Maksymilian Alojzy':
                {'imie':'Maksymilian', 'imie2': 'Alojzy', 'nazwisko':'Füger von Rechtborn'},
            'Frovinus z Nowego Sącza':
                {'imie':'Frovinus'},
            'Franko z Polski':
                {'imie':'Franko'},
            'Elżbieta-Wiola':
                {'imie':'Elżbieta', 'imie2': 'Wiola'},
            'Duhamel de Prècourt':
                {'nazwisko':'Duhamel de Prècourt'},
            'Del Bene':
                {'nazwisko':'Del Bene'},
            'Deffilles du Jan Ignacy':
                {'imie':'Jan', 'imie2': 'Ignacy', 'nazwisko':'du Deffilles'},
            'Bye de Mikołaj':
                {'imie':'Mikołaj', 'nazwisko':'de Bye'},
            'Bolesław III Mały':
                {'imie':'Bolesław'},
            'Bolesław III Hojny':
                {'imie':'Bolesław'},
            'Bolesław Pobożny':
                {'imie':'Bolesław'},
            'Bolesław I Chrobry':
                {'imie':'Bolesław'},
            'Bolesław Mieszkowic':
                {'imie':'Bolesław'},
            'Bolesław II Szczodry':
                {'imie':'Bolesław'},
            'Bolesław III Krzywousty':
                {'imie':'Bolesław'},
            'Bolesław Kędzierzawy':
                {'imie':'Bolesław'},
            'Bolesław Wstydliwy':
                {'imie':'Bolesław'},
            'Bolesław Wysoki':
                {'imie':'Bolesław'},
            'Bolesław Łysy':
                {'imie':'Bolesław'},
            'Bokum ab Alten Jan Henryk':
                {'imie':'Jan', 'imie2': 'Henryk', 'nazwisko':'Bokum ab Alten'},
            'Andrzej zw. Andrzejem z Krakowa':
                {'imie':'Andrzej'},
            'Aleksy de Lekenstein':
                {'imie':'Aleksy', 'nazwisko':'de Lekenstein'},
            'Bona Sforza':
                {'imie':'Bona', 'nazwisko':'Sforza'},
            'Albrecht Hohenzollern':
                {'imie':'Albrecht', 'nazwisko':'Hohenzollern'},
            'Albrecht Fryderyk Hohenzollern':
                {'imie':'Albrecht', 'imie2':'Fryderyk', 'nazwisko':'Hohenzollern'},
            'Abraham Judaeus Bohemus':
                {'imie':'Abraham', 'nazwisko':'Bohemus'},
            'Arnold de Caucina':
                {'imie':'Arnold', 'nazwisko':'de Caucina'},
            'Baudouin de Courtenay':
                {'nazwisko':'Baudouin de Courtenay'},
            'Baudouin de Courtenay Jan': 
                {'imie':'Jan', 'nazwisko':'Baudouin de Courtenay'},
            'Baudouin de Courtenay Romualda':
                {'imie':'Romualda', 'nazwisko':'Baudouin de Courtenay'},
            'Cynerski Rachtamowicz Jan':
                {'imie':'Jan', 'imie2':'', 'nazwisko':'Cynerski', 'nazwisko2':'Rachtamowicz'},
            'Demko Michajłowicz':
                {'imie':'Demko', 'imie2':'', 'nazwisko':'Michajłowicz'},
            'Dziersław Abrahamowic':
                {'imie':'Dziersław', 'nazwisko':'Abrahamowic'},
            'Hersch Pesach-Libman':
                {'imie':'Pesach', 'imie2':'Libman', 'nazwisko':'Hersch'},
            'Krupecki Aleksander Oleksowicz':
                {'imie': 'Aleksander', 'nazwisko':'Krupecki'},
            'Krupka Przecławski Konrad':
                {'imie': 'Konrad', 'nazwisko':'Krupka', 'nazwisko2':'Przecławski'},
            'Licinius Namysłowski Jan':
                {'imie': 'Jan', 'nazwisko':'Licinius', 'nazwisko2':'Namysłowski'},
            'Maryna Mniszchówna':
                {'imie': 'Maryna', 'nazwisko':'Mniszchówna'},
            'Słupica Bogdan Bohuszewicz':
                {'imie': 'Bogdan', 'nazwisko':'Słupica'},
            'Słupica Hrehory Bohuszewicz':
                {'imie': 'Hrehory', 'nazwisko':'Słupica'},
            'Sołtan Aleksandrowicz':
                {'nazwisko':'Sołtan'},
            'Sołtan Iwan Aleksandrowicz':
                {'imie': 'Iwan', 'nazwisko':'Sołtan'},
            'Elżbieta Aleksiejewna':
                {'imie': 'Elżbieta', 'nazwisko':'Aleksiejewna'},
            'Jadwiga Andegaweńska':
                {'imie': 'Jadwiga', 'nazwisko':'Andegaweńska'},
            'Połubiński Iwan Andrejewicz':
                {'imie': 'Iwan', 'nazwisko':'Połubiński'},
            'Połubiński Wasyl Andrejewicz':
                {'imie': 'Wasyl', 'nazwisko':'Połubiński'},
            'Łazarz Andrysowic':
                {'imie': 'Łazarz', 'nazwisko':'Andrysowic'},
            'Kijeński van der Noot Stanisław':
                {'imie': 'Stanisław', 'nazwisko':'Kijeński', 'nazwisko2': 'van der Noot'},
            'Abraham ben Joszijahu z Trok':
                {'imie': 'Abraham'},
            'd’Alifio Ludwik':
                {'imie': 'Ludwik', 'nazwisko':'d’Alifio'},
            'd’Aloy Jan Baptysta':
                {'imie': 'Jan', 'imie2':'Baptysta', 'nazwisko':'d’Aloy'},
            'Anna ks. Teck':
                {'imie': 'Anna'},
            'Aqua Andrzej dell’':
                {'imie': 'Andrzej', 'nazwisko':"dell’Aqua"},
            'Dawid ben Samuel':
                {'imie': 'Dawid'},
            'Eliasz ben Salomon':
                {'imie': 'Eliasz'},
            'Erceville d’ Stefan':
                {'imie': 'Stefan', 'nazwisko':'d’Erceville'},
            'Ezra ben Nisan':
                {'imie': '', 'nazwisko':''},
            'Fedor kn. Neswizki':
                {'imie': 'Fedor'},
            'Gallot d’Angers':
                {'nazwisko':'Gallot d’Angers'},
            'Ganier d’Aubin Paweł':
                {'imie': 'Paweł', 'nazwisko':'Ganier', 'nazwisko2':'d’Aubin'},
            'Gerlach von Kulpen':
                {'nazwisko':'Gerlach von Kulpen'},
            'Goświn lub Jozwin':
                {'nazwisko':'Goświn'},
            'Izrael ben Eliezer':
                {'imie': 'Izrael'},
            'Izrael ben Mosze':
                {'imie': 'Izrael'},
            'Jakub Josef Ben Zebi Ha’kohen':
                {'imie': 'Jakub', 'imie2':'Josef'},
            'Jakub ben Zeew':
                {'imie': 'Jakub', 'nazwisko':''},
            'Jehuda Chassid ha-Lewi':
                {'imie': 'Jehuda', 'nazwisko':'Chassid ha-Lewi'},
            'Joanna księżna łowicka':
                {'imie': 'Joanna'},
            'Józef ben Jeszua':
                {'imie': 'Józef'},
            'Kierdej Jan – Said bej':
                {'imie': 'Jan', 'nazwisko':'Kierdej'},
            'Kocmyrzowski von Lorenzberg Stanisław Mateusz':
                {'imie': 'Stanisław', 'imie2':'Mateusz', 'nazwisko':'Kocmyrzowski', 'nazwisko2': 'von Lorenzberg'},
            'Lehman Berman ben Naftali Katz':
                {'imie': 'Lehman'},
            'Lipski Antoni Jan Nepomucen Wojciech':
                {'imie': 'Antoni', 'imie2':'Jan', 'imie3':'Nepomucen', 'imie4':'Wojciech', 'nazwisko':'Lipski'},
            'Ludwik ks. Wirtemberski':
                {'imie': 'Ludwik'},
            'Marcin zwany Kułab z Tarnowca':
                {'imie': 'Marcin'},
            'Mikołaj vel Mikuł':
                {'imie': 'Mikołaj'},
            'Mordechaj ben Nisan':
                {'imie': 'Mordechaj'},
            'Obberghen Antoni van':
                {'imie': 'Antoni', 'nazwisko':'van Obberghen'},
            'Patruus Jan ojciec':
                {'imie': 'Jan', 'nazwisko':'Patruus'},
            'Patruus Jan syn':
                {'imie': 'Jan', 'nazwisko':'Patruus'},
            'Paweł von Züllen':
                {'imie': 'Paweł', 'nazwisko':'von Züllen'},
            'Podhorodeński Paweł Łukasz Jan Kanty':
                {'imie':'Paweł', 'imie2':'Łukasz', 'imie3':'Jan', 'imie4':'Kanty', 'nazwisko':'Podhorodeński'},
            'Poll von Pollenburg Franciszek Antoni':
                {'imie': 'Franciszek', 'imie2':'Antoni', 'nazwisko':'Poll von Pollenburg'},
            'Pollak Franciszek Karol Józef Ernest':
                {'imie': 'Franciszek', 'imie2':'Karol', 'imie3':'Józef', 'imie4':'Ernest', 'nazwisko':'Pollak'},
            'Potocki Karol lub Jan Karol':
                {'imie': 'Karol', 'nazwisko':'Potocki'},
            'Sabbataj ben Jozef':
                {'imie': 'Sabbataj'},
            'Schack von Wittenau Karol Albrecht':
                {'imie': '', 'nazwisko':''},
            'Spira Natan Nata ben Salomon':
                {'imie': 'Spira', 'imie2':'Natan', 'imie3':'Nata'},
            'Szania ben Szachna':
                {'imie': 'Szania'},
            'Szantyr Stanisław August Ursyn':
                {'imie': 'Stanisław', 'imie2':'August', 'imie3':'Ursyn', 'nazwisko':'Szantyr'},
            'Szeptycki Stanisław Maria Jan Teofil':
                {'imie': 'Stanisław', 'imie2':'Maria','imie3':'Jan', 'imie4':'Teofil', 'nazwisko':'Szeptycki'},
            'Szymon h. Zaremba':
                {'imie': 'Szymon'},
            'Świeszewski Jan Alojzy Jakub Bonawentura':
                {'imie': 'Jan', 'imie2':'Alojzy', 'imie3':'Jakub', 'imie4':'Bonawentura', 'nazwisko':'Świeszewski'},
            'Śwircz Adam zwany Jarosz z Husiatyna i Olchowca':
                {'imie': 'Adam', 'nazwisko':'Śwircz'},
            'Tchorznicki Mniszek Konstanty Maria Aleksander':
                {'imie': 'Konstanty', 'imie2':'Maria', 'imie3':'Aleksander', 'nazwisko':'Tchórznicki', 'nazwisko2': 'Mniszek'},
            'Tchórznicki Mniszek Józef Engelbert Ignacy':
                {'imie': 'Józef', 'imie2':'Engelbert', 'imie3':'Ignacy', 'nazwisko':'Tchórznicki', 'nazwisko2': 'Mniszek'},
            'Ludwik I Andegaweński Wielki':
                {'imie':'Ludwik'},
            'Bernacki':
                {'nazwisko':'Bernacki'},
            'Andrzej Bobola':
                {'imie:':'Andrzej', 'nazwisko':'Bobola'},
            'Świeborowski Żak Mikołaj':
                {'imie':'Mikołaj', 'nazwisko':'Świeborowski', 'nazwisko2':'Żak'},
            'Pełka Ząbr z Czyżowa':
                {'imie':'Pełka', 'nazwisko':'Ząbr'},
            'Sabbataj ben Meir ha-Kohen':
                {'imie':'Sabbataj'},
            'Cilli Alessandro da Pistoia':
                {'imie':'Alessandro', 'nazwisko':'Cilli', 'nazwisko2':'da Pistoia'},
            'Pastorius ab Hirtenberg Joachim':
                {'imie':'Joachim', 'nawisko':'Pastorius ab Hirtenberg'},
            'Linde Adrian von der':
                {'imie':'Adrian', 'nazwisko':'von der Linde'},
            'Linde Jan von der':
                {'imie':'Jan', 'nazwisko':'von der Linde'}, 
            'Linde Jan Ernest von der':
                {'imie':'Jan', 'nazwisko':'von der Linde'},
            'Linde Łukasz von der':
                {'imie':'Łukasz', 'nazwisko':'von der Linde'},
            'Osten von der Ulryk':
                {'imie':'Ulryk', 'nazwisko':'von der Osten'},
            'Rennen Salomon von der':
                {'imie':'Salomon', 'nazwisko':'von der Rennen'},
            'Korsak Jan Kazimierz Zaleski':
                {'imie':'Jan', 'imie2':'Kazimierz', 'nazwisko':'Korsak', 'nazwisko2':'Zaleski'},
            'Andronicus Łukasz Klimkowski':
                {'ime':'Łukasz', 'nazwisko':'Andronicus', 'nazwisko2':'Klimkowski'},
            'Jan II Kazimierz Waza':
                {'imie':'Jan', 'imie2':'Kazimierz', 'nazwisko':'Waza'},
            'Jan Albert Waza':
                {'imie':'Jan', 'imie2':'Albert', 'nazwisko':'Waza'},
            'Karol Ferdynand':
                {'imie':'Karol', 'imie2':'Ferdynand'},
            'Kawecka-Ladojska':
                {'nazwisko':'Kawecka-Ladojska'},
            'Aleksander Olelko':
                {'imie':'Aleksander', 'nazwisko':'Olelko'},
            'Aleksander Jagiellończyk':
                {'imie':'Aleksander','nazwisko':'Jagiellończyk'},
            'Anna Jagiellonka':
                {'imie':'Anna', 'nazwisko':'Jagiellonka'},
            'Arquien de la Grange Anna Ludwik ':
                {'imie':'Anna', 'imie2:':'Ludwik', 'nazwisko':'d’Arquien', 'nazwisko2':'de la Grange'},
            'Badowski Kłoda Józef':
                {'imie':'Józef', 'nazwisko':'Badowski', 'nazwisko2':'Kłoda'},
            'Barbara Jagiellonka':
                {'imie':'Barbara', 'nazwisko':'Jagiellonka'},
            'Barbara Zapolya':
                {'imie':'Barbara', 'nazwisko':'Zapolya'},
            'Barbara Radziwiłłówna':
                {'imie':'Barbara', 'nazwisko':'Radziwiłłówna'},
            'Bojarski Czarnota Kajetan Henryk':
                {'imie':'Kajetan', 'imie2':'Henryk', 'nazwisko':'Bojarski', 'nazwisko2':'Czarnota'},
            'Bokum ab Alten Jan Henryk':
                {'imie':'Jan', 'imie2':'Henryk', 'nazwisko':'Bokum ab Alten'},
            'Bykowski Jaksa Antoni Jerzy':
                {'imie':'Antoni', 'imie2':'Jerzy', 'nazwisko':'Bykowski', 'nazwisko2':'Jaksa'},
            'Bykowski Jaksa Ignacy':
                {'imie':'Ignacy', 'nazwisko':'Bykowski', 'nazwisko2':'Jaksa'},
            'Bykowski Jaksa Jan':
                {'imie':'Jan', 'nazwisko':'Bykowski', 'nazwisko2':'Jaksa'},
            'Bykowski Jaksa Juliusz':
                {'imie':'Juliusz', 'nazwisko':'Bykowski', 'nazwisko2':'Jaksa'},
            'Bykowski Jaksa Piotr':
                {'imie':'Piotr', 'nazwisko':'Chołoniewski', 'nazwisko2':'Myszka'},
            'Bykowski Jaksa Stanisław':
                {'imie':'Stanisław', 'nazwisko':'Bykowski', 'nazwisko2':'Jaksa'},
            'Bykowski Jaksa Witold':
                {'imie':'Witold', 'nazwisko':'Bykowski', 'nazwisko2':'Jaksa'},
            'Chołoniewski Myszka Adam':
                {'imie':'Adam', 'nazwisko':'Chołoniewski', 'nazwisko2':'Myszka'},
            'Chołoniewski Myszka Antoni':
                {'imie':'Antoni', 'nazwisko':'Chołoniewski', 'nazwisko2':'Myszka'},
            'Chołoniewski Myszka Edward':
                {'imie':'Edward', 'nazwisko':'Chołoniewski', 'nazwisko2':'Myszka'},
            'Chołoniewski Myszka Ignacy':
                {'imie':'Ignacy', 'nazwisko':'Chołoniewski', 'nazwisko2':'Myszka'},
            'Chołoniewski Myszka Ksawery':
                {'imie':'Ksawery', 'nazwisko':'Chołoniewski', 'nazwisko2':'Myszka'},
            'Chołoniewski Myszka Rafał':
                {'imie':'Rafał', 'nazwisko':'Chołoniewski', 'nazwisko2':'Myszka'},
            'Chołoniewski Myszka Stanisław':
                {'imie':'Stanisław', 'nazwisko':'Chołoniewski', 'nazwisko2':'Myszka'},
            'Chołoniewski Myszka Władysław':
                {'imie':'Władysław', 'nazwisko':'Chołoniewski', 'nazwisko2':'Myszka'},
            'Chronowski Jaxa Alojzy':
                {'imie':'Alojzy', 'nazwisko':'Chronowski', 'nazwisko2':'Jaxa'},
            'Chronowski Jaxa Eustachy': 
                {'imie':'Eustachy', 'nazwisko':'Chronowski', 'nazwisko2':'Jaxa'},
            'Del Buono Paweł':
                {'imie':'Paweł', 'nazwisko':'Del Buono'},
            'Del Bene':
                {'nazwisko':'Del Bene'},
            'Del Pace Rafał':
                {'imie':'Rafał', 'nazwisko':'Del Pace'},
            'Deybel de Hammerau Krystian Godfryd':
                {'imie':'Krystian', 'imie2':'Krystian', 'nazwisko':'Deybel de Hammerau'}, 
            'Długoszewski Wieniawa Ignacy':
                {'imie':'Ignacy', 'nazwisko':'Długoszewski', 'nazwisko2':'Wieniawa'},
            'Dobrawa':
                {'imie':'Dobrawa'},
            'Doruchowski Wierzbięta Jakub':
                {'imie':'Jakub', 'imie2':'Wierzbięta','nazwisko':'Doruchowski'},
            'Drucki Iwan Baba':
                {'imie':'Iwan', 'nazwisko':'Drucki'},
            'Drucki Iwan Putiata':
                {'imie':'Iwan', 'nazwisko':'Drucki'},
            'Drucki Iwan Krasny':
                {'imie':'Iwan', 'nazwisko':'Drucki'},
            'Drucki Semen Dymitrowicz':
                {'imie':'Semen', 'nazwisko':'Drucki'},
            'Drucki Wasyl Semenowicz Krasny':
                {'imie':'Wasyl', 'nazwisko':'Drucki'}, 
            'Dunin ze Skrzyńska':
                {'imie':'Dunin'},
            'Dunka de Sajo Władysław':
                {'imie':'Władysław', 'nazwisko':'Dunka de Sajo'},
            'Elżbieta Jagiellonka':
                {'imie':'Elżbieta', 'nazwisko':'Jagiellonka'},
            'Etgens de Etgenson Władysław':
                {'imie':'Władysław', 'nazwisko':'Etgens', 'nazwisko2':'de Etgenson'},
            'Francus de Franco':
                {'imie':'Francus', 'nazwisko':'de Franco'},
            'Heydatel Rothuill Jan':
                {'imie':'Jan', 'nazwisko':'Heydatel', 'nazwisko2':'Rothuill'},
            'Jacobson Jedlina Wojciech':
                {'imie':'Wojciech', 'nazwisko':'Jacobson'},
            'Jacobson Jakub a Gehema':
                {'imie':'Jakub', 'nazwisko':'Jacobson'},
            'Jadwiga Jagiellonka':
                {'imie':'Jadwiga', 'nazwisko':'Jagiellonka'},
            'Jakub Świnka':
                {'imie':'Jakub', 'nazwisko':'Świnka'},
            'Jan Albert Waza':
                {'imie':'Jan', 'imie2':'Albert', 'nazwisko':'Waza'},
            'Konaszewicz Sahajdaczny Piotr':
                {'imie':'Piotr', 'nazwisko':'Konaszewicz', 'nazwisko2':'Sahajdaczny'},
            'Kunzek von Lichton August': 
                {'imie':'August', 'nazwisko':'Kunzek von Lichton'},
            'La Roche Skalski Kazimierz de':
                {'imie':'Kazimierz', 'nazwisko':'de La Roche', 'nazwisko2':'Skalski'},
            'Mroczko Nagórka z Kisielewa':
                {'imie':'Mroczko', 'nazwisko':'Nagórka'},
            'Onesyfor Dziewoczka':
                {'imie':'Onesyfor', 'nazwisko':'Dziewoczka'},
            'Quirini de Saalbrück Eugeniusz':
                {'imie':'Eugeniusz', 'nazwisko':'Quirini de Saalbrück'},
            'Stanisław Stary':
                {'imie':'Stanisław', 'nazwisko':'Stary'},
            'Sulisław Gryfita':
                {'imie':'Sulisław'},
            'Sulisław Bernatowic':
                {'imie':'Sulisław', 'nazwisko':''},
            'Szaniawska ze Scipionów Anna':
                {'imie':'Anna', 'nazwisko':'Szaniawska'},
            'Szturm de Sztrem Edward': 
                {'imie':'Edward', 'nazwisko':'Szturm de Sztrem'},
            'Szturm de Sztrem Tadeusz Jan':
                {'imie':'Tadeusz', 'imie2':'Jan', 'nazwisko':'Szturm de Sztrem'},
            'Szturm de Sztrem Witold':
                {'imie':'Witold', 'nazwisko':'Szturm de Sztrem'},
            'Szturm de Sztrem Zofia': 
                {'imie':'Zofia', 'nazwisko':'Szturm de Sztrem'},
          }
