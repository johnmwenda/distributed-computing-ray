import requests

def downloadfile(name,url):
    name=name+".mp4"
    r=requests.get(url)
    print("****Connected****")
    f=open(name,'wb');
    print("Donloading.....")
    for chunk in r.iter_content(chunk_size=255): 
        if chunk: # filter out keep-alive new chunks
            f.write(chunk)
    print("Done")
    f.close()

url = 'https://video.fnbo9-1.fna.fbcdn.net/v/t39.25447-2/448023068_3495783580713661_6001331868924686188_n.mp4?_nc_cat=110&ccb=1-7&_nc_sid=9a5d50&efg=eyJ2ZW5jb2RlX3RhZyI6ImRhc2hfaDI2NC1iYXNpYy1nZW4yXzEwODBwIiwidmlkZW9faWQiOjQ3NzQ3MTA0MTM2NDgwM30%3D&_nc_ohc=0leKP2aUTWMQ7kNvgFWflfH&_nc_ht=video.fnbo9-1.fna&oh=00_AYA8dOLu1PDrq5c8L7DT5d5IMN9fjq2Y1Ff0pn27HsKy5A&oe=6670FB50'
downloadfile('announcement', url)