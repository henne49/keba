# keba
  
Project to load the last charging session from a Keba C Wallbox, that has no usable web interface. The program allows to display the sessions as a html page and exporting them as CSV File. You can define rfid tags for different cars and it allows to export Company Car Sessions separately. 

The Heavy Lifting Code was done by Stephan, https://github.com/fiebrandt Credits to his work. 

Currently AMD64 Image only TODO create an ARM64 Image for MAC M1

<img width="1200" alt="grafik" src="https://github.com/henne49/keba/assets/4662326/2fe74e79-eccf-421f-9b00-bbc1284d693a">


## create a data folder
```
mkdir data 
pwd
```
## docker or podman
```
docker run --publish 5050:5000 -e KEBA_WALLBOX_IP=MYIP -e KEBA_WALLBOX_PORT=7090 -e ENERGY_PRICE=0.49 -e COMPANYCAR='Company Car' ghcr.io/henne49/keba:latest
```

## docker-compose file:
create a host folder data, where the json file (database) and the rfid file are stored. So you can export and backup your charging history. 

The energy price is always written for the latest 30 charging sessions, older session will stay with old pricing in the json file. 
```
  keba:
    image: ghcr.io/henne49/keba:latest
    container_name: keba
    restart: unless-stopped
    environment:
      - KEBA_WALLBOX_IP=MY_IP
      - KEBA_WALLBOX_PORT=7090
      - ENERGY_PRICE=0.49
      - COMPANYCAR=Company Car
     ports:
      - "5050:5000"
    volumes:
      - /YOURPATHTODATAFOLDER/data:/data
```

## rfids.json file
multiple RFID Token can be specified for private and company car stored in your data folder.

```
{
    "0000000000000000" : "Private Car",
    "1111111111111111" : "Company Car",
    "2222222222222222" : "Company Car"
}
```
