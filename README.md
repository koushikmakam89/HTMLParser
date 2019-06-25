# HTML Parser
It builds HTML for an given JSON data and HTML template 

## Who it works

We need to provide the HTML Parser two inputs
* HTML template
* JSON data
    , on init

On calling the *generateHTML* method we will get an HTML generated for the JSON data provided

#### The template is as follows *{{JSONProperty}}* for flat objects and for iteratables *{{JSONProperty[#].ChildProperty}}*

,we can overide both the patterns using *setIterationIdentifer* and *setTemplatePattern* respectively 

## Example
There is an sample template and JSON , to generate sample template just run 

```python
python3 src/main.py
```


