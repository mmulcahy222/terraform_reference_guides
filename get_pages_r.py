
import json
import os
import re
from helpers import *
from bs4 import BeautifulSoup
from jinja2 import Template


class Cloud:
    @property
    def local_directory(self):
        return f'redacted'
    @property
    def local_json_directory(self):
        return self.local_directory + "json/"
class AmazonAWS(Cloud):
    provider_id = '8847'
    cloud_name = 'amazon_aws'
    terraform_url_part = 'aws'
class MicrosoftAzure(Cloud):
    provider_id = '8835'
    cloud_name = 'microsoft_azure'
    terraform_url_part = 'azurerm'
class GoogleCloud(Cloud):
    provider_id = '8708'
    cloud_name = 'google_cloud'
    terraform_url_part = 'google'
class ProviderResources():
    '''
    This represents the page/json file that has all of the resource IDS & other resource information/nodes
    '''
    def __init__(self,cloud_object):
        self.cloud_object = cloud_object
    def get_resources_json(self):
        provider_id = self.cloud_object.provider_id
        cloud_name = self.cloud_object.cloud_name
        provider_directory = f'C:/makeshift/files/terraform/clouds/{cloud_name}/'
        provider_full_path = provider_directory + f'provider_{cloud_name}.json'
        if(os.path.exists(provider_full_path)):
            print(f'LOCAL FILE SYSTEM> Retrieving contents from {provider_full_path}')
            return json.loads(file_get_contents(provider_full_path))
        all_resources_url = f'https://registry.terraform.io/v2/provider-versions/{provider_id}?include=provider-docs'
        all_resources_json = get_html(all_resources_url)
        file_put_contents(provider_full_path,all_resources_json)
        print(f'INTERNET REQUEST> Retrieving contents from {all_resources_url}')
        return json.loads(all_resources_json)
class ResourceData():
    '''
    This represents the page/json file containing JSON data (such as the actual Terraform configuration)
    '''
    def __init__(self,cloud_object):
        self.cloud_object = cloud_object
    def get_resource_json(self,resource_id,resource_slug):
        cloud_name = self.cloud_object.cloud_name
        resource_directory_json = f'C:/makeshift/files/terraform/clouds/{cloud_name}/json/'
        resource_data_full_path = resource_directory_json + f'{resource_slug}.json'
        if(os.path.exists(resource_data_full_path)):
            print(f'LOCAL FILE SYSTEM> Retrieving contents from {resource_data_full_path}')
            return json.loads(file_get_contents(resource_data_full_path))
        resource_data_url = f'https://registry.terraform.io/v2/provider-docs/{resource_id}'
        resource_data_json = get_html(resource_data_url)
        print(resource_data_url)
        file_put_contents(resource_data_full_path,resource_data_json)
        print(f'INTERNET REQUEST> Retrieving contents from {resource_data_url}')
        return json.loads(resource_data_json)
    def get_terraform_text(self,markdown_content):
        example_usage_index = markdown_content.find("Example Usage")
        content_border = '```'
        starting_quotes_index = markdown_content.find(content_border,example_usage_index)
        ending_quotes_index = markdown_content.find(content_border,starting_quotes_index+len(content_border))
        #the three represents the HCL you don't want to see
        terraform_text = markdown_content[starting_quotes_index+len(content_border)+3:ending_quotes_index]
        #put a breaking space ONLY in the beginning of each line
        
        #REMOVES THE PROBLEM OF too may spaces after the closing curly bracket.
        terraform_text = re.sub('}\n+','}\n',terraform_text)
        # terraform_text = re.sub('"\s+','"',terraform_text)
        #Puts in Non Breaking Space only in the beginning, and not on every single space
        terraform_text = re.sub('\n\s+',lambda x: "\n" + "&nbsp;" * len(x.group(0)) * 2,terraform_text)
        #web formatting
        terraform_text = terraform_text.strip('\n').replace("\n","<br/>")
        set_clipboard(terraform_text)
        return terraform_text.strip()

def retrieve_files(cloud_object):
    '''
    Gets the Provider JSON (with all the resources) and the JSON files from that provider file
    '''
    provider_resources = ProviderResources(cloud_object)
    resource_data_object = ResourceData(cloud_object)
    resources_json = provider_resources.get_resources_json()
    resources_nodes = resources_json.get("included")
    for resources_node in resources_nodes:
        resource_id = resources_node.get("id")
        resource_slug = resources_node.get("attributes", {}).get("slug", {})
        resource_title = resources_node.get("attributes", {}).get("title", {}).replace("_", " ").title()
        resource_category = resources_node.get("attributes", {}).get("title", {})
        resource_data = resource_data_object.get_resource_json(resource_id,resource_slug)
        resource_content = resource_data.get("data",{}).get("attributes",{}).get("content",{})


#Generate Page

cloud_object = GoogleCloud()
resource_data_object = ResourceData(cloud_object)
files = os.listdir(cloud_object.local_json_directory)
resource_nodes = []
count = 0
for file in files:
    slug = file.split(".")[0]
    resource_full_path = cloud_object.local_json_directory + file
    resource_json = json.loads(file_get_contents(resource_full_path))
    print(f"{count}) GETTING FILE IN {resource_full_path}")
    attributes = resource_json.get("data",{}).get("attributes",{})
    markdown_content = attributes.get("content",{})
    resource_title = attributes.get("title",{})
    terraform_text = resource_data_object.get_terraform_text(markdown_content)
    #web_format
    terraform_text = terraform_text.replace("\n","<br/>")
    url = f'https://registry.terraform.io/providers/hashicorp/{cloud_object.terraform_url_part}/latest/docs/resources/{slug}'
    resource_nodes.append({"url":url,"resource_title":resource_title,"terraform_text":terraform_text})    
    count += 1
    # if count == 4:
    #     break
template = Template(file_get_contents('terraform_template.j2'))
html = template.render(resource_nodes=resource_nodes)
file_put_contents('terraform_guide.html', html)