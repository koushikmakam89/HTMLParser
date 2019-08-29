import lxml.html as lh
from lxml import etree


class HTMLParser():

    """
    Method to parse HTML template with JSON data 
    """

    _iterationIdentifer = '[#]'
    _groupIdentifer = '[$]'
    _childObjectFinder = '.'
    _templatePrefix = '{{'
    _templateSufix = '}}'

    def __init__(self, htmltemplate, jsonData):
        self.data = jsonData
        self.template = htmltemplate

    def _jsonValue(self, htmlValue, index, elimater):
        splitPrefixValue = htmlValue.split(self.getIterater())[
            index].replace(' ', '')
        splitPrefixList = splitPrefixValue.split(elimater)
        return splitPrefixList[index+1].replace(' ', '').lower()

    def getIterater(self):
        return self._iterationIdentifer + self._childObjectFinder

    def _getParentName(self, htmlValue):
        return self._jsonValue(htmlValue, 0, self._templatePrefix)

    def _getChildName(self, htmlValue):
        return self._jsonValue(htmlValue, -1, self._templateSufix)

    def _getChildName(self, htmlValue):
        val = htmlValue.split(self.getIterater())[-1]
        return val.rstrip(self._templateSufix).lower()

    def _replaceRowData(self, rowInformation, jsonArrayName, htmlElementsList):
        popupaledRow = ""
        if jsonArrayName in self.data:
            for data in self.data[jsonArrayName]:
                rowData = rowInformation
                for element in htmlElementsList:
                    innerElement = element.split(self._templatePrefix)
                    innerElementList = []
                    for item in innerElement:
                        if item.find(self._iterationIdentifer) > -1 and item.find(self._templateSufix) > -1:
                            val = item.split(self._templateSufix)[0]
                            innerElementList.append(
                                self._templatePrefix+val+self._templateSufix)
                    for innerElement in innerElementList:
                        key = self._getChildName(innerElement)
                        if key in data.keys():
                            rowData = rowData.replace(
                                innerElement, str(data[key]))
                        rowData = self._addFlatData(
                            rowData, data, (jsonArrayName+self._iterationIdentifer))
                popupaledRow = popupaledRow + rowData
        return popupaledRow

    def _replaceGroupRowData(self, rowInformation, jsonArrayName, htmlElementsList, sortOrder):
        popupaledRow = ""
       
        if jsonArrayName in self.data:
            sortedList = self.data[jsonArrayName]

            reversedSortList = sortOrder[::-1] 
            for item in reversedSortList:
                sortedList = sorted(
                    sortedList, key=lambda i: i[item], reverse=False)

            #Make groups
            prevValue = ''
            groups = {}
            for item in sortedList:
                if item[sortOrder[0]] == prevValue:
                    groups[prevValue].append(item)
                else:
                    prevValue = item[sortOrder[0]]
                    groups[prevValue] = []
                    groups[prevValue].append(item)
            
            for key in groups.keys():
                index = 0
                metaData = dict()
                coloumOrder = []
                popupaledGorupRow = ''
                for data in groups[key]:
                    rowData = rowInformation
                    for element in htmlElementsList:
                        index = index + 1
                        innerElement = element.split(self._templatePrefix)
                        innerElementList = []
                        for item in innerElement:
                            if (item.find(self._iterationIdentifer) > -1 or
                                    item.find(self._groupIdentifer)) and item.find(self._templateSufix) > -1:
                                val = item.split(self._templateSufix)[0]
                                innerElementList.append(
                                    self._templatePrefix+val+self._templateSufix)

                        for innerElement in innerElementList:
                            key = self._getChildName(innerElement.replace(
                                self._groupIdentifer, self._iterationIdentifer))

                            if index <= len(htmlElementsList):
                                coloumOrder.append(key)

                            if key in data.keys():
                                val = str(data[key])

                                if key in metaData.keys():
                                    if val in metaData[key]:
                                        metaData[key][val] = metaData[key][val] + 1
                                    else:
                                        metaData[key][val] = 1
                                else:
                                    metaData[key] = dict()
                                    metaData[key][val] = 1

                                rowData = rowData.replace(innerElement, val)
                            rowData = self._addFlatData(
                                rowData, data, (jsonArrayName+self._iterationIdentifer))

                    popupaledGorupRow = popupaledGorupRow + rowData

                # Modify the current table structure
                cache = dict()
                row_elements = lh.fromstring(popupaledGorupRow).xpath('//tr')
                for row_element in row_elements:
                    oldRowValue = etree.tostring(row_element).decode()
                    newDataValue = ''
                    oldDataValue = ''
                    index = -1
                    td_elements = lh.fromstring(oldRowValue).xpath('//td')
                    for td in td_elements:
                        index = index + 1
                        oldDataValue = oldDataValue + etree.tostring(td).decode()

                        # logic for rowspan
                        if coloumOrder[index] in sortOrder:
                            rowSpan = metaData[coloumOrder[index]][td.text]
                            if index not in cache.keys():
                                cache[index] = []
                            if td.text not in cache[index]:
                                td.set('rowspan', str(rowSpan))
                            else:
                                td.set('style', 'display:none;')
                            cache[index].append(td.text)

                        newDataValue = newDataValue + etree.tostring(td).decode()
                    newRowValue = oldRowValue.replace(oldDataValue, newDataValue, 1)
                    popupaledGorupRow = popupaledGorupRow.replace(oldRowValue, newRowValue, 1)
                    
                popupaledRow = popupaledRow + popupaledGorupRow

        return popupaledRow

    def _addRecordsToTable(self, content):
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
                    # we have data to iterate
                    thingToReplace = etree.tostring(r).decode()
                    row_element = lh.fromstring(thingToReplace)
                    td_element = row_element.xpath('//td')

                    td_data = []
                    sortOrder = []

                    for d in td_element:
                        content = d.text_content()
                        if content.find(self._groupIdentifer) > -1:
                            sortOrder.append(self._getChildName(
                                content.replace(self._groupIdentifer, self._iterationIdentifer)))
                        td_data.append(content)
                    if len(sortOrder) > 0:
                        datarows = self._replaceGroupRowData(thingToReplace,
                                                             self._getParentName(htmlValue=next(
                                                                 sub for sub in td_data if sub)
                                                                 .replace(self._groupIdentifer, self._iterationIdentifer)),
                                                             td_data, sortOrder)
                    else:
                        datarows = self._replaceRowData(thingToReplace,
                                                        self._getParentName(htmlValue=next(
                                                            sub for sub in td_data if sub)
                                                            .replace(self._groupIdentifer, self._iterationIdentifer)),
                                                        td_data)

                    # Remove the table if the datarow content is empty
                    if datarows != '':
                        modifiedData = modifiedData.replace(
                            thingToReplace, datarows)
                    else:
                        modifiedData = modifiedData.replace(
                            etree.tostring(t).decode(), '')

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
                                                self._getParentName(
                                                    htmlValue=li_data[0] if len(li_data) > 0 else ''),
                                                li_data)
                    modifiedData = modifiedData.replace(thingToReplace, data)
        return modifiedData

    def _addFlatData(self, content, jsonData, root=''):
        """

        Method to replace data from all flat records

        Args
            HTML template

        Output
            The HTML template replace with all flat JSON data

        """
        def replaceContent(content, data, key):
            mykey = key if root == '' else root + self._childObjectFinder + key
            htmlValue = self._templatePrefix + mykey + self._templateSufix
            content = content.replace(htmlValue, str(data[key]))
            return content

        if isinstance(jsonData, dict):
            for key in jsonData.keys():
                if isinstance(jsonData[key], dict):
                    content = self._addFlatData(content, jsonData[key], key)
                elif not isinstance(jsonData[key], list):
                    content = replaceContent(content, jsonData, key)
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
        htmlContent = self._addRecordsToList(htmlContent, '//ul')
        htmlContent = self._addRecordsToList(htmlContent, '//ol')
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
        Iteration Identifer =  '[$]'
    """

    self._groupIdentifer = groupIdentifer

def setTemplatePattern(self, prefix='{{', sufix='}}'):
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
