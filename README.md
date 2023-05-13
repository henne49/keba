# keba
docker-compose file:

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

rfid file, multiple RFID Token can be specified for private and company car


```
{
    "0000000000000000" : "Private Car",
    "1111111111111111" : "Company Car",
    "2222222222222222" : "Company Car"
}
```
