""" skrypt uzupełnia etykiety typów jednostek administracyjnych """

import os
import sys
from pathlib import Path
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_core
from dotenv import load_dotenv
from wikidariahtools import find_name_qid, statement_value_fix


# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'


# --------------------------------- MAIN ---------------------------------------

if __name__ == "__main__":
    # login i hasło ze zmiennych środowiskowych (plik .env w folderze ze źródłami)
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)

    ok, p_ontohgis_database_id = find_name_qid('ontohgis database id', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'ontohgis database id' w instancji Wikibase")
        sys.exit(1)

    lista = [
                ('Q83841','Q83568'), ('Q83726','Q83582'), ('Q83637','Q83532'),
                ('Q83600','Q83534'), ('Q83593','Q83543'), ('Q83124','Q80425'),
                ('Q83126','Q80416'), ('Q83975','Q83926'), ('Q83979','Q83527'),
                ('Q83992','Q83943'), ('Q83992','Q83943'), ('Q84016','Q83640'),
                ('Q84022','Q83583'), ('Q84065','Q83526'), ('Q84124','Q84097'),
                ('Q84129','Q83713'), ('Q84180','Q83789'), ('Q84181','Q83895'),
                ('Q84192','Q84071'), ('Q84224','Q83799'), ('Q84259','Q84219'),
                ('Q84306','Q83806'), ('Q84341','Q84055'), ('Q84349','Q84226'),
                ('Q84376','Q83851'), ('Q84383','Q84172'), ('Q84392','Q84042'),
                ('Q84417','Q83563'), ('Q84431','Q84102'), ('Q84435','Q84218'),
                ('Q84447','Q83571'), ('Q84491','Q83843'), ('Q84498','Q83935'),
                ('Q84529','Q84432'), ('Q84549','Q83863'), ('Q84568','Q83778'),
                ('Q84613','Q84344'), ('Q84621','Q84004'), ('Q84630','Q83835'),
                ('Q84649','Q84539'), ('Q84652','Q84150'), ('Q84661','Q83934'),
                ('Q84669','Q83696'), ('Q84673','Q84405'), ('Q84714','Q84510'),
                ('Q84733','Q84474'), ('Q84735','Q84218'), ('Q84751','Q83919'),
                ('Q84754','Q84229'), ('Q84788','Q84381'), ('Q84791','Q84171'),
                ('Q84812','Q83555'), ('Q84814','Q83552'), ('Q84825','Q84427'),
                ('Q84837','Q84338'), ('Q84896','Q83704'), ('Q84908','Q84856'),
                ('Q84910','Q84523'), ('Q84933','Q84797'), ('Q84935','Q83885'),
                ('Q84950','Q84189'), ('Q84953','Q83934'), ('Q84972','Q83722'),
                ('Q85009','Q83777'), ('Q85011','Q83774'), ('Q85015','Q84939'),
                ('Q85022','Q83575'), ('Q85032','Q84299'), ('Q85041','Q83702'),
                ('Q85044','Q84924'), ('Q85085','Q84956'), ('Q85107','Q84122'),
                ('Q85115','Q84918'), ('Q85123','Q84671'), ('Q85129','Q85019'),
                ('Q85158','Q85064'), ('Q85179','Q84298'), ('Q85191','Q84858'),
                ('Q85203','Q84720'), ('Q85208','Q85084'), ('Q85220','Q84604'),
                ('Q85230','Q83590'), ('Q85243','Q83904'), ('Q85244','Q84890'),
                ('Q85251','Q85154'), ('Q85254','Q85227'), ('Q85273','Q84532'),
                ('Q85281','Q83819'), ('Q85295','Q83786'), ('Q85304','Q85286'),
                ('Q85313','Q84400'), ('Q85331','Q83964'), ('Q85340','Q83667'),
                ('Q85344','Q84151'), ('Q85352','Q84142'), ('Q85353','Q85270'),
                ('Q85359','Q85035'), ('Q85371','Q84895'), ('Q85381','Q83850'),
                ('Q85383','Q83725'), ('Q85388','Q83742'), ('Q85392','Q85026'),
                ('Q85393','Q84831'), ('Q85396','Q85020'), ('Q85402','Q85164'),
                ('Q85407','Q84624'), ('Q85420','Q84485'), ('Q85422','Q84861'),
                ('Q85439','Q83890'), ('Q85442','Q85176'), ('Q85458','Q83765'),
                ('Q85471','Q84370'), ('Q85480','Q84794'), ('Q85488','Q85317'),
                ('Q85519','Q84505'), ('Q85537','Q84108'), ('Q85550','Q85057'),
                ('Q85553','Q84722'), ('Q85555','Q85347'), ('Q85580','Q84867'),
                ('Q85598','Q84546'), ('Q85603','Q84195'), ('Q85612','Q84723'),
                ('Q85629','Q85441'), ('Q85635','Q84480'), ('Q85650','Q83807'),
                ('Q85667','Q85030'), ('Q85677','Q85498'), ('Q85682','Q84762'),
                ('Q85688','Q83653'), ('Q85696','Q83655'), ('Q85704','Q84186'),
                ('Q85708','Q85110'), ('Q85717','Q84461'), ('Q85722','Q85073'),
                ('Q85726','Q83984'), ('Q85738','Q83660'), ('Q85761','Q84594'),
                ('Q85762','Q85658'), ('Q85763','Q83538'), ('Q85773','Q85195'),
                ('Q85775','Q84285'), ('Q85778','Q83733'), ('Q85783','Q84580'),
                ('Q85798','Q85330'), ('Q85809','Q85269'), ('Q85817','Q84940'),
                ('Q85818','Q84802'), ('Q85819','Q83555'), ('Q85825','Q85685'),
                ('Q85827','Q83673'), ('Q85832','Q84343'), ('Q85848','Q84838'),
                ('Q85850','Q83633'), ('Q85853','Q84994'), ('Q85854','Q84375'),
                ('Q85877','Q85599'), ('Q85898','Q83792'), ('Q85901','Q83932'),
                ('Q85905','Q85333'), ('Q85919','Q84841'), ('Q85922','Q85167'),
                ('Q85924','Q83678'), ('Q85930','Q85881'), ('Q85948','Q85259'),
                ('Q85950','Q85554'), ('Q85951','Q83970'), ('Q85955','Q85474'),
                ('Q85975','Q84027'), ('Q85983','Q83923'), ('Q85993','Q84515'),
                ('Q86001','Q83865'), ('Q86014','Q84486'), ('Q86016','Q83877'),
                ('Q86023','Q85939'), ('Q86024','Q85074'), ('Q86029','Q85791'),
                ('Q86277','Q86080'), ('Q86244','Q86080'), ('Q86197','Q86162')
    ]

    for item in lista:
        item_1, item_2 = item

        wb_item_1 = wbi_core.ItemEngine(item_id=item_1)
        label_1 = wb_item_1.get_label('pl')
        wb_item_2 = wbi_core.ItemEngine(item_id=item_2)
        label_2 = wb_item_2.get_label('pl')

        ontohgis_id_1 = ''
        for statement in wb_item_1.statements:
            prop_nr = statement.get_prop_nr()
            if prop_nr == p_ontohgis_database_id:
                statement_value = statement.get_value()
                statement_type = statement.data_type
                ontohgis_id_1 = statement_value_fix(statement_value, statement_type)
                break

        ontohgis_id_2 = ''
        for statement in wb_item_2.statements:
            prop_nr = statement.get_prop_nr()
            if prop_nr == p_ontohgis_database_id:
                statement_value = statement.get_value()
                statement_type = statement.data_type
                ontohgis_id_2 = statement_value_fix(statement_value, statement_type)
                break

        wikibase_1 = f'https://prunus-208.man.poznan.pl/wiki/Item:{item_1}'
        wikibase_2 = f'https://prunus-208.man.poznan.pl/wiki/Item:{item_2}'

        print(f'{item_1},{label_1},{ontohgis_id_1},{wikibase_1},{item_2},{label_2},{ontohgis_id_2},{wikibase_2}')


    print("Skrypt wykonany")
