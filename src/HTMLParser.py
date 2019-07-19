import lxml.html as lh
from lxml import etree
from collections import defaultdict
import string
import random

class HTMLParser():

    """
    Method to parse HTML template with JSON data 
    """
    
    _iterationIdentifer='[#]'
    _groupIdentifer='[$]'
    _childObjectFinder='.'
    _templatePrefix='{{'
    _templateSufix='}}'

    def __init__(self,htmltemplate,jsonData):
        self.data = jsonData
        self.template = htmltemplate

    def _jsonValue(self,htmlValue,index,elimater):
        splitPrefixValue = htmlValue.split(self.getIterater())[index].replace(' ','')
        splitPrefixList = splitPrefixValue.split(elimater)
        return splitPrefixList[index+1].replace(' ','').lower()
      

    def getIterater(self):
        return self._iterationIdentifer + self._childObjectFinder

    def _getParentName(self,htmlValue):
        return self._jsonValue(htmlValue,0,self._templatePrefix)
    
    def _getChildName(self,htmlValue):
        return self._jsonValue(htmlValue,-1,self._templateSufix)

    """
    This might be useful in the feature
    """
    def _groupBy(self,result,json,groupList,index,parent='',parentItem=''):
        localParent = parent
        localParentItem = parentItem
        item = groupList[index]
        for obj in json:
            if localParent != '':
                if obj[localParentItem] == localParent:
                    newkey = obj[item]
                    if obj[item] not in result[localParent]['child']:
                        result[localParent]['child'][newkey] = {
                            'records':[],
                            'child':{},
                            'selector':item
                        }
                    result[localParent]['child'][newkey]['records'].append(obj)
            else:  
                newkey = obj[item] 
                if obj[item] not in result.keys():
                    result[newkey] = {
                        'records':[],
                         'child':{},
                         'selector':item
                    }
                result[newkey]['records'].append(obj)

        index = index+1
        if len(groupList) == index :
            return result
        else:
            for key in result.keys():
                self._groupBy(result,json,groupList,index,key,item)
    
    def _groupJson(self,jsonArrayName,groupList):
        groups = {}
        index = 0
        def childIterator(groups,json,index,item):
            for obj in json:
                item = groupList[index]
                key = obj[item]
                if key not in groups.keys():
                    groups[key] = {
                        'child':{},
                        'records':[]
                    }
                groups[key]['records'].append(obj)
            return groups

        if jsonArrayName in self.data:
           
            groups = childIterator(groups,self.data[jsonArrayName],index,groupList[index])
            index = index+1 
            for item in range(len(groupList)-1):
                for key in groups.keys():
                    obj = groups[key]
                    record = groups[key]['records']
                    if index > 1 :
                        for i in range(index):
                            if obj != None:
                                for childKey in obj.keys():
                                    if childKey not in ['records','child']:
                                        obj[childKey]['child'] = childIterator(obj[childKey]['child'],obj['records'],index,groupList[index])
                                if bool(obj) == True:
                                    obj = obj.get('child')
                                    record = obj.get('records')
                    elif bool(obj) == True:
                        obj = childIterator(obj,record,index,groupList[index])
                index = index + 1 
        return groups

    def randomString(self,stringLength=5):
        """Generate a random string of fixed length """
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(stringLength))

    def _generatRowSpanRows(self,groups,rowInformation,maxlevel,level,ignoreKeys,remainingRecords):
        trElement = lh.fromstring(rowInformation).xpath('//tr')[0]
        row = '<tr class="{}" style="{}">'.format(trElement.get('styles'),trElement.get('class'))+'{}</tr>{}'
        result = ""
        tdElements = (trElement).xpath('//td')
        level = level + 1
        
        for key in groups.keys():
            if key not in ignoreKeys:
                rowData = ''
                element = tdElements[level]
                groupCount = 1
                uniqurRecordCount = 0

                uniqueRecords = defaultdict(int)
                for item in groups[key]['records']:
                    uniqueRecords[str(item)] += 1

                if len(uniqueRecords) > 1:
                    for _ in uniqueRecords.keys():
                        uniqurRecordCount = uniqurRecordCount+1
                
                if groupCount > 1 :
                    rowspan = groupCount+uniqurRecordCount - level
                else:
                    rowspan = groupCount+uniqurRecordCount 
                
                if uniqurRecordCount == len(groups[key]['records']):
                    groupCount  = uniqurRecordCount
                
                if len(groups[key]['records'])>groupCount:
                    groupCount = len(groups[key]['records'])

                element.set('rowspan',str(rowspan))
                element.text = key
                rowData = rowData + etree.tostring(element).decode()
                insertPoint = ''
                uniqueKey = self.randomString()

                #Add the remaining td data if row span is less then max row count 
                if maxlevel != groupCount:
                    insertPoint = '##{}##'.format(uniqueKey)
                    item  = groups[key]['records'][0]
                    trElement = lh.fromstring(rowInformation).xpath('//tr')[0]
                    tdElements = (trElement).xpath('//td')
                    for element in tdElements[(level+1):len(tdElements)]:
                        htmlselector = element.text_content()
                        htmlselector = htmlselector.replace(self._groupIdentifer,self._iterationIdentifer)
                        element.text = item[self._getChildName(htmlselector)]
                        rowData  = rowData + etree.tostring(element).decode()
                
                    listDetails  = []

                    for rec in groups[key]['records']:
                        if str(rec) != str(item):
                            listDetails.append(rec)
                    
                    remainingRecords[uniqueKey] = {
                        'level': level+1,
                        'records':listDetails
                    }
                
                
                result = result + row.format(rowData,insertPoint)
                nextLevel = False
                for childKey in groups[key]:
                    if childKey not in ignoreKeys: 
                        nextLevel = True
                        break
                if nextLevel == True:
                    result = result + self._generatRowSpanRows(groups[key],rowInformation,maxlevel,level,ignoreKeys,remainingRecords)
        return result

    def _addRemainingRows(self,rowInformation,html,jsonList):
        for key in jsonList.keys():
            selector = '##{}##'.format(key)
            if html.find(selector) > -1:
                trElement = lh.fromstring(rowInformation).xpath('//tr')[0]
                row = '<tr class="{}" style="{}">'.format(trElement.get('styles'),trElement.get('class'))+'{}</tr>'
                record = ''
                for data in jsonList[key]['records']:
                    trElement = lh.fromstring(rowInformation).xpath('//tr')[0]
                    tdElements = (trElement).xpath('//td')
                    rowData = ''
                    level = jsonList[key]['level']
                    for element in tdElements[level:len(tdElements)]:
                        htmlselector = element.text_content()
                        htmlselector = htmlselector.replace(self._groupIdentifer,self._iterationIdentifer)
                        element.text = data[self._getChildName(htmlselector)]
                        rowData  = rowData + etree.tostring(element).decode()
                    record  = record + row.format(rowData)
                html = html.replace(selector,record)

        return html
            
    def _replaceGroupRowData(self,rowInformation,jsonArrayName,htmlElementsList,groupList):
        records = ""
        _ignoreKeys = ['records','child']
        groups  =  self._groupJson(jsonArrayName,groupList)
        
        for key in groups.keys():
            #__init__
            remainingRecords = {}
            spanRecords = ''
            group = {}
            group[key] = groups[key]
            maxDataLength = 0
           
            maxDataLength = len(group[key]['records'])
            spanRecords = self._generatRowSpanRows(group,rowInformation,maxDataLength,-1,_ignoreKeys,remainingRecords)
            spanRecords = self._addRemainingRows(rowInformation,spanRecords,remainingRecords)
            records = records + spanRecords

        return records

    def _replaceRowData(self,rowInformation,jsonArrayName,htmlElementsList):
        popupaledRow = ""
        if jsonArrayName in self.data:
            for data in self.data[jsonArrayName]:
                rowData = rowInformation
                for element in htmlElementsList:
                    innerElement = element.split(self._templatePrefix)
                    innerElementList = []
                    for item in innerElement:
                        if item.find(self._iterationIdentifer)>-1 and item.find(self._templateSufix)>-1:
                            val = item.split(self._templateSufix)[0]
                            innerElementList.append(self._templatePrefix+val+self._templateSufix)
                    for innerElement in innerElementList:
                        rowData = rowData.replace(innerElement,data[self._getChildName(innerElement)])
                popupaledRow = popupaledRow  + rowData
        return popupaledRow

    def _addRecordsToTable(self,content):
        """

        Method to replace data from table records

        Args
            HTML template
        
        Output
            The HTML template with tables replace with JSON data

        """
        doc = lh.fromstring(content)
        modifiedData = etree.tostring(doc).decode()
        table_elements = doc.xpath('//table')
        for t in table_elements:
            table_element = lh.fromstring(etree.tostring(t).decode())
            tr_elements = table_element.xpath('//tr')
            for r in tr_elements:
                row = r.text_content()
                if row.find(self.getIterater()) > -1:
                    #we have data to iterate
                    thingToReplace = etree.tostring(r).decode()
                    row_element = lh.fromstring(thingToReplace)
                    td_element = row_element.xpath('//td')
                    
                    # table flow records
                    td_data = []
                    sortOrder = []

                    for d in td_element:
                        content = d.text_content()
                        if content.find(self._groupIdentifer)> -1:
                            sortOrder.append(self._getChildName(
                                content.replace(self._groupIdentifer,self._iterationIdentifer)))
                        td_data.append(content)
                    if len(sortOrder) > 0:
                        datarows = self._replaceGroupRowData(thingToReplace,
                            self._getParentName(htmlValue = 
                                    next(sub for sub in td_data if sub)
                                    .replace(self._groupIdentifer,self._iterationIdentifer)),
                            td_data,sortOrder)
                    else:
                        datarows = self._replaceRowData(thingToReplace,
                                self._getParentName(htmlValue = 
                                        next(sub for sub in td_data if sub)
                                        .replace(self._groupIdentifer,self._iterationIdentifer)),
                                td_data)
                    modifiedData = modifiedData.replace(thingToReplace, datarows)
                    
        return modifiedData

    def _addRecordsToList(self, content, elementSelector):
        """

        Method to replace data from list records

        Args
            HTML template
            List type example //ul
        
        Output
            The HTML template with list replace with JSON data

        """

        doc = lh.fromstring(content)
        modifiedData = etree.tostring(doc).decode()
        list_elements = doc.xpath(elementSelector)
        for l in list_elements:
            if l.text_content().find(self.getIterater()) > -1:
                thingToReplace = etree.tostring(l).decode()
                list_element = lh.fromstring(thingToReplace)
                li_elements = list_element.xpath('//li')
                li_data = []
                for d in li_elements:
                    li_data.append(d.text_content())
                
                for li_text in li_elements:
                    thingToReplace = etree.tostring(li_text).decode()
                    data = self._replaceRowData(thingToReplace,
                                self._getParentName(htmlValue = li_data[0] if len(li_data)>0 else ''),
                                li_data)
                    modifiedData = modifiedData.replace(thingToReplace,data)
        return modifiedData

    def _addFlatData(self,content,jsonData,root=''):
        """

        Method to replace data from all flat records

        Args
            HTML template
        
        Output
            The HTML template replace with all flat JSON data

        """
        def replaceContent(content, data , key):
            mykey = key if root == '' else root + self._childObjectFinder + key
            htmlValue = self._templatePrefix + mykey + self._templateSufix
            content = content.replace(htmlValue,str(data[key]))
            return content
        
        if isinstance(jsonData, dict):
            for key in jsonData.keys():
                if isinstance(jsonData[key], dict):
                    content = self._addFlatData(content,jsonData[key],key)
                elif not isinstance(jsonData[key], list) :
                    content = replaceContent(content,jsonData,key)
        return content


    def generateHTML(self):
        """

        Wrapper to call all types of HTML elemnt pharsers

        Args
            HTML template
            Json Data
        
        Output
            The HTML template with JSON data replaced

        """
        
        htmlContent = self._addRecordsToTable(self.template)
        htmlContent = self._addRecordsToList(htmlContent,'//ul')
        htmlContent = self._addRecordsToList(htmlContent,'//ol')
        htmlContent = self._addFlatData(htmlContent, self.data)
        return htmlContent
    
def setIterationIdentifer(self, iterationIdentifer='[#]'):
    """
        Method to set the itearion identifer

        Args
            New identifier value

        Default 
        Iteration Identifer =  '[#]'
    """

    self._iterationIdentifer = iterationIdentifer

def setGroupIdentifer(self, groupIdentifer='[#]'):
    """
        Method to set the group-by identifer

        Args
            New identifier value

        Default 
        Iteration Identifer =  '[#]'
    """

    self._groupIdentifer = groupIdentifer

def setTemplatePattern(self,prefix='{{',sufix='}}'):
    """
        Method to set the template pattern

        Args
            Prefix value 
            Sufix value
        
        Default 
            Prefix = '{{'
            Sufix = '}}'
    """
    self._templatePrefix = prefix
    self._templateSufix = sufix

