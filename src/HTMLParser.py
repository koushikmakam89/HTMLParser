import lxml.html as lh
from lxml import etree

class HTMLParser():

    """
    Method to parse HTML template with JSON data 
    """
    
    _iterationIdentifer='[#]'
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

    def _replaceRowData(self,rowInformation,jsonArrayName,htmlElementsList):
        popupaledRow = ""
        if jsonArrayName in self.data:
            for data in self.data[jsonArrayName]:
                rowData = rowInformation
                for element in htmlElementsList:
                    rowData = rowData.replace(element,data[self._getChildName(element)])
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
        modifiedData = content
        doc = lh.fromstring(content)
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
                    td_data = []
                    
                    for d in td_element:
                        td_data.append(d.text_content())

                    modifiedData = modifiedData.replace(thingToReplace,
                        self._replaceRowData(thingToReplace,
                            self._getParentName(htmlValue = td_data[0] if len(td_data)>0 else ''),
                            td_data))
    
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

