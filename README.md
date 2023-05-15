# keba
docker-compose file:
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
    volumes:
      - $DOCKERDIR/keba:/data
```

rfids.json file, multiple RFID Token can be specified for private and company car
stored in your data folder.

```
{
    "0000000000000000" : "Private Car",
    "1111111111111111" : "Company Car",
    "2222222222222222" : "Company Car"
}
```
