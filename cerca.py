#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import unicodedata
import datetime
import urllib.request
import ast
import xml.etree.ElementTree as ET

from math import radians, cos, sin, asin, sqrt


class Esdeveniment:
    def __init__(self):
        self.nom = ''
        self.adreca = ''
        self.dataInici = ''
        self.dataFi = ''
        self.hora = ''
        self.horaFi = ''
        #llista de parells (distancia, adreça de l'estació)
        self.estacionsAparcament = None
        self.estacionsBicis = None



def haversine(lon1, lat1, lon2, lat2):
    # converteix graus decimals a radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # formula de haversine
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # radi de la terra en km
    return c * r


def proximitatData(p,dataSort):
    dt_obj = datetime.datetime.strptime(p[0], '%d/%m/%Y') #converteix a timestamp
    data2 = dt_obj.timestamp()
    return abs(dataSort-data2) #valor de proximitat a la data

def getEstacions(distance,latAct,lonAct,rootB,aparcament):
    estacions = []
    #per cada estacio de la branca del XML on estan totes
    for estacio in rootB.findall('station'):
        latStation = float(estacio.find('lat').text)
        lonStation = float(estacio.find('long').text)
        #calcula distancia al acte
        distanceToAct = round(haversine(lonStation,latStation,lonAct,latAct) * 1000)
        #per aparcament busca slots
        if aparcament:
            query = estacio.find('slots').text
        else:
            query = estacio.find('bikes').text
        #si hi han llocs i està a la distancia demanada
        if(int(query) > 0 and distanceToAct<=distance):
            adreca = estacio.find('street').text
            streetNumber = estacio.find('streetNumber').text
            if(streetNumber is None):
                adreca += " s/n"
            else:
                adreca += " " + streetNumber
            estacions.append((distanceToAct,adreca))

    #si es troba alguna estació, les retorna ordenades(per distancia)
    if(estacions != []):
        return sorted(estacions)
    else:
        return []


def printHeadHTML():
    print("<!DOCTYPE html>\n<html>\n<head>\n<style>")
    print("table {\n  font-family: arial, sans-serif;")
    print("  border-collapse: collapse;\n  width: 100%;\n}\n")

    print("td, th {\n  border: 1px solid #dddddd;")
    print("  text-align: left;\n  padding: 8px;\n}\n")

    print("tr:nth-child(even) {\n  background-color: #dddddd;")
    print("}\n</style>\n</head>\n<body>\n")

    print("<h2>Esdeveniments trobats</h2>\n")

def printHeaderTable(diaris):
    print("<table>\n<tr>")
    print("<th> Nom </th>")
    print("<th>Adre&ccedil;a</th>")
    if diaris:
        print("<th>Hora fi</th>")
        print("<th colspan='5'>Estacions amb aparcament</th>")
        print("<th colspan='5'>Estacions amb bicicletes</th>")
    else:
        print("<th>Data inici</th>")
        print("<th>Data final</th>")
        print("<th>Hora</th>")
    print("</tr>")


def printSolution(mapaId,listDataId,diaris):
    printHeadHTML()
    printHeaderTable(diaris)

    table = []

    #per cada esdeveniment de la llista, que ara està ordenada(mensuals)
    for p in listDataId:
        #appends per la sortida en HTML
        table.append("\t<tr>\n")
        td = []
        
        #p[1] es l'id
        esd = mapaId[p[1]]

        td.append("<td>" + esd.nom + "</td>\n\t\t")
        td.append("<td>" + esd.adreca + "</td>\n\t\t")
        if diaris:
            td.append("<td>" + esd.horaFi + "</td>\n\t\t")
            count = 0
            for estacio in esd.estacionsAparcament:
                #estacio es un pair distancia, adreça
                td.append("<td>" + estacio[1] + " (" + str(estacio[0]) + "m)" + "</td>\n\t\t")
                count+=1
                if (count == 5):
                    #com a maxim 5
                    break
            for x in range(count,5):
                td.append("<td></td>\n\t\t") #omplir llocs buits

            count = 0
            for estacio in esd.estacionsBicis:
                td.append("<td>" + estacio[1] + " (" + str(estacio[0]) + "m)" + "</td>\n\t\t")
                count+=1
                if (count == 5):
                    break
            for x in range(count,5):
                td.append("<td></td>\n\t\t") #omplir llocs buits
        else:
            td.append("<td>" + esd.dataInici + "</td>\n\t\t")
            td.append("<td>" + esd.dataFi + "</td>\n\t\t")
            td.append("<td>" + esd.hora + "</td>\n\t\t")

        table.append("\t\t"+"".join(td))
        table.append("\n\t</tr>\n")


    #posa el final del HTML
    table.append("</table>")
    print("".join(table))
    print("</body>\n</html>")

def evalElement(key,acte,lloc,barri):
    if isinstance(key,list):  
        return evalList(key,acte,lloc,barri)
    elif isinstance(key,tuple):
        return evalTuple(key,acte,lloc,barri)
    else:
        return evalString(key,acte,lloc,barri)

def evalList(key,acte,lloc,barri):
    for element in key:
        if not evalElement(element,acte,lloc,barri):
            #si algú no compleix alguna condició, el descarta
            return False
    return True

def evalTuple(key,acte,lloc,barri):
    for element in key:
        if evalElement(element,acte,lloc,barri):
            #si es compleix alguna condicio, el mostra
            return True
    return False

def evalString(key,acte,lloc,barri):
    #treure accents
    keyNorM = unicodedata.normalize('NFKD',key).encode('ASCII','ignore')
    #tot a minuscules
    keyNor = keyNorM.decode("utf-8").upper().lower()
    return (keyNor in acte) or (keyNor in barri) or (keyNor in lloc)

def evalActe(acte,diaris,key,dataSort):
    acteNom = acte.find("nom").text
    llocSimple = acte.find("lloc_simple")
    llocNom = llocSimple.find("nom").text
    barriNom = llocSimple.find("adreca_simple").find("districte").text
    if barriNom is None:
        return False #si no te barri li falten atributs al acte en el XML
    #treure accents
    acteNomNorM = unicodedata.normalize('NFKD',acteNom).encode('ASCII','ignore')
    llocNomNorM = unicodedata.normalize('NFKD',llocNom).encode('ASCII','ignore')
    barriNomNorM = unicodedata.normalize('NFKD',barriNom).encode('ASCII','ignore')
    #tot a minuscules
    acteNomNor = acteNomNorM.decode("utf-8").upper().lower()
    llocNomNor = llocNomNorM.decode("utf-8").upper().lower()
    barriNomNor = barriNomNorM.decode("utf-8").upper().lower()

    #descarta els esdeveniments que no estan entre data inici i data final
    #també els que no tenen data d'inici
    if not diaris:
        dataIniciStr = acte.find("data").find("data_inici").text
        dataFiStr = acte.find("data").find("data_fi").text
        error_fi=False
        if dataIniciStr is None:
            return False
        if dataFiStr is None:
            #no te fi
            error_fi=True

        #data d'inici del acte a timestamp, per fer la comparació
        dtInici_obj = datetime.datetime.strptime(dataIniciStr,'%d/%m/%Y')
        dataInici = dtInici_obj.timestamp()

        if not error_fi:
            #data fi a timestamp, per fer la comparació
            dtFi_obj = datetime.datetime.strptime(dataFiStr,'%d/%m/%Y')
            dataFi = dtFi_obj.timestamp()
            if (dataSort < dataInici or dataSort > dataFi):
                return False
        elif dataSort < dataInici:
            return False

    #una vegada pasada la selecció per data, ara selecciona pel key
    return evalElement(key,acteNomNor,llocNomNor,barriNomNor)


def main():
    now = datetime.datetime.now()
    actualDate = str(now.day) + "/" + str(now.month) + "/" + str(now.year)

    #missatges de help
    helpKey = " Select all activities that have KEY as the name of the event,"
    helpKey += " the name of the place where it takes place or"
    helpKey += " district. To set more than one query key, you can either set a list,"
    helpKey += " which will show the activities that satisfy all the keys; or"
    helpKey += " a tuple that will show the activities that satisfy some of the keys."
    helpKey += " There is no distinction between uppercase and lowercase letters,"
    helpKey += " nor between accented and unaccented. Simple commas should be used"
    helpKey += " to start and end the queries, double for the string"

    helpData = "Date 'dd/mm/aaaa' that selects the events for which DATE"
    helpData += " is between your start and end date, otherwise"
    helpData += " it shows the event of the current day"

    helpDistance = "If the query is about daily events, indicate"
    helpDistance += " the maximum distance in meters that Bicing's stations"
    helpDistance += " are showed. In the case that DATE is displayed"
    helpDistance += " does not show any station so this parameter"
    helpDistance += " is not required. Default value: 500m"

    #definició de parametres
    parser = argparse.ArgumentParser()
    parser.add_argument('--key', help=helpKey, required=True)
    parser.add_argument('--date', help=helpData, default=actualDate)
    parser.add_argument('--distance', help=helpDistance, default=500)

    #tracta parametres

    args = vars(parser.parse_args())

    key = ast.literal_eval(args["key"])

    dataArg = args["date"]

    distance = int(args["distance"])

    diaris=False

    #determina si es consultaran actes diaris o mensuals
    dataSort=0
    if dataArg == actualDate:
        diaris=True
        #per poder passar-ho com a parametre després
    else:
        #converteix data a timestamp, per poder ordenar
        dt_obj = datetime.datetime.strptime(dataArg, '%d/%m/%Y')
        dataSort = dt_obj.timestamp()

    #conecta amb la pàgina corresponent
    if diaris:
        sock = urllib.request.urlopen("http://w10.bcn.es/APPS/asiasiacache/peticioXmlAsia?id=199") 
    else:
        sock = urllib.request.urlopen("http://w10.bcn.es/APPS/asiasiacache/peticioXmlAsia?id=103")

    xmlSource = sock.read()                            
    sock.close()
    root = ET.fromstring(xmlSource)


    if (root.find("body").find("resultat") is None):
        #per si el XML dels actes diaris no funciona durant la nit
        print("ERROR: No es pot trobar l'informacio dels actes d'avui, sisplau torni a intentar-ho m&eacutes tard")
        exit()

    #branca del XML amb tots els actes
    actes = root.find("body").find("resultat").find("actes")

    #XML bicicletes
    sockB = urllib.request.urlopen("https://wservice.viabicing.cat/v1/getstations.php?v=1") 
    xmlSourceB = sockB.read()
    sockB.close()
    rootB = ET.fromstring(xmlSourceB)

    mapaId = {} #mapa de id a Esdeveniment
    listDataId = []

    for acte in actes.findall('acte'):
        if evalActe(acte,diaris,key,dataSort): #si l'acte compleix les condicions
            esd = Esdeveniment()
            adrecaObject = acte.find("lloc_simple").find("adreca_simple")
            adreca = adrecaObject.find("carrer").text
            adreca += " "
            adreca += adrecaObject.find("numero").text

            esd.nom = acte.find("nom").text
            esd.adreca = adreca

            if diaris:
                #troba coordenades, per les estacions
                coord = adrecaObject.find("coordenades").find("googleMaps")
                lat = coord.attrib['lat']
                lon = coord.attrib['lon']
                #troba la hora fi, sinó interrogant
                horaFi = acte.find("data").find("hora_fi").text
                if horaFi is None:
                    horaFi = "?"
                esd.horaFi = horaFi
                #crida els mètodes per les estacions, que retornen llistes ordenades
                esd.estacionsAparcament = getEstacions(distance,float(lat),
                                                       float(lon),rootB,True)
                esd.estacionsBicis = getEstacions(distance,float(lat),
                                                 float(lon),rootB,False)
            else:
                #pels mensuals, cerca el atributs data d'inici, data final, hora
                dataInici = acte.find("data").find("data_inici").text

                dataFi = acte.find("data").find("data_fi").text
                if dataFi is None:
                    dataFi = "?"

                hora = acte.find("data").find("hora_inici").text
                if hora is None:
                    hora = "?"

                esd.dataInici = dataInici
                esd.dataFi = dataFi
                esd.hora = hora

            ident = acte.find("id").text
            #posa l'acte al mapa
            mapaId[ident]=esd
            if diaris:
                #string buit perque sigui compatible amb els mensuals, que s'han d'ordenar
                listDataId.append(("",ident))
            else:
                listDataId.append((dataInici,ident)) #llista de parells dataInici,identificador d'esdeveniment

    #si no s'ha modificat listDataId cap esdeveniment satisfà les condicions
    if(listDataId==[]):
        print("ERROR: No s'ha trobat cap esdeveniment que compleixi les condicions de cerca")
        exit()

    if(not diaris):
        #ordena segons la proximitat a la data solicitada:
        listDataId.sort(key=lambda p:proximitatData(p,dataSort))
        #lambda, per crear una funció que agrupi els dos parametres
        #ja que key es crida únicament per cada element de listDataId

    printSolution(mapaId,listDataId,diaris)


#crida la funcio principal de l'script
main()
