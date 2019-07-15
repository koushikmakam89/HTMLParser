import lxml.html as lh
from lxml import etree

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

    def getIterater(self):
        return self._iterationIdentifer + self._childObjectFinder

    def _getParentName(self,htmlValue):
        val = htmlValue.split(self.getIterater())[0]
        return val.lstrip(self._templatePrefix).lower()
    
    def _getChildName(self,htmlValue):
        val = htmlValue.split(self.getIterater())[-1]
        return val.rstrip(self._templateSufix).lower()

    def _replaceRowData(self,rowInformation,jsonArrayName,htmlElementsList,sortOrder = []):
        def sort(json):
            if len(sortOrder) > 0:
                for item in sortOrder:
                    newlist = sorted(json, key=lambda record: record[item], reverse=True)
                return newlist
            return json

        popupaledRow = ""
        if jsonArrayName in self.data:
            json = self.data[jsonArrayName]
            json = sort(json)
            for data in json:
                rowData = rowInformation
                for element in htmlElementsList:
                    selectorElement = element.replace(self._groupIdentifer,self._iterationIdentifer)
                    rowData = rowData.replace(element,data[self._getChildName(selectorElement)])
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
            #print(etree.tostring(t))
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
                    groupIndex=[]
                    sortOrder = []

                    index = 0
                    for d in td_element:
                        content = d.text_content()
                        if content.find(self._groupIdentifer)> -1:
                            groupIndex.append(index)
                            sortOrder.append(self._getChildName(
                                content.replace(self._groupIdentifer,self._iterationIdentifer)))
                        td_data.append(content)
                        index +=  1
                    datarows = self._replaceRowData(thingToReplace,
                            self._getParentName(htmlValue = 
                                    next(sub for sub in td_data if sub)
                                    .replace(self._groupIdentifer,self._iterationIdentifer)),
                            td_data,sortOrder)
                    
                    #Code to add rowspans for grouped records
                    if len(groupIndex) > 0:
                        row_element = lh.fromstring(datarows).xpath('//tr')
                        td_element = lh.fromstring(etree.tostring(row_element[0]).decode()).xpath('//td')
                        for index in groupIndex:
                            element = td_element[index]
                            oldRecord = etree.tostring(element).decode()
                            counter = datarows.count(element.text_content())
                            td_element[index].set("rowspan",str(counter))
                            newRecord = etree.tostring(element).decode()
                            datarows = datarows.replace(oldRecord,newRecord,1)
                            datarows = datarows.replace(oldRecord,'')

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

        modifiedData = content
        doc = lh.fromstring(content)
        list_elements = doc.xpath(elementSelector)
        for l in list_elements:
            if l.text_content().find(self.getIterater()) > -1:
                thingToReplace = etree.tostring(l).decode()
                list_element = lh.fromstring(thingToReplace)
                li_elements = list_element.xpath('//li')
                li_data = []
                for d in li_elements:
                    li_data.append(d.text_content())
                modifiedData = modifiedData.replace(thingToReplace,
                        self._replaceRowData(thingToReplace,
                            self._getParentName(htmlValue = li_data[0] if len(li_data)>0 else ''),
                            li_data))


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

