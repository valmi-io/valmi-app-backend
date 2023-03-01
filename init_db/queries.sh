## get my spaces
curl -o - -v  --header "Authorization: Bearer b88344cf801c2820ead65a513987d995fffc72cf" "http://localhost:8000/api/v1/spaces/"


##credential create
curl -o - -v  -d '{"connector_type":"DEST_WEBHOOK","connector_config":"{\"hostname\": \"localhost\", \"port\": 5432}", "name": "first credential nae"}' -X POST --header "Content-Type: application/json" --header "Authorization: Bearer b88344cf801c2820ead65a513987d995fffc72cf" "http://localhost:8000/api/v1/workspaces/c72607a7-f11f-41b7-9ac5-a11869bb512c/credentials/create"


#sources create
curl -o - -v  -d '{"credential_id":"a42281b6-920f-4d63-9804-45db96bf1029","catalog":"{\"catalog_test\":true}" , "name": "my_first_source"}' -X POST --header "Content-Type: application/json" --header "Authorization: Bearer b88344cf801c2820ead65a513987d995fffc72cf" "http://localhost:8000/api/v1/workspaces/c72607a7-f11f-41b7-9ac5-a11869bb512c/sources/create"

#destination create
curl -o - -v  -d '{"credential_id":"cca686d1-8128-49a2-8d07-34975c192fb9","catalog":"{\"catalog_test\":true}" , "name": "my_first_destination"}' -X POST --header "Content-Type: application/json" --header "Authorization: Bearer b88344cf801c2820ead65a513987d995fffc72cf" "http://localhost:8000/api/v1/workspaces/c72607a7-f11f-41b7-9ac5-a11869bb512c/destinations/create"

#sync create
curl -X 'POST' \
  'http://localhost:8000/api/v1/workspaces/c72607a7-f11f-41b7-9ac5-a11869bb512c/syncs/create' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer b88344cf801c2820ead65a513987d995fffc72cf' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "string",
  "source_id": "94675fda-a235-4513-8934-8c73228b693d",
  "destination_id": "4f23544d-dc6a-4901-9b1b-494423b86544",
  "schedule": "{\"type\":\"cron\",\"value\":\"0 0 0 0 0\"}"
}'

#get syncs
curl -o - -v  --header "Content-Type: application/json" --header "Authorization: Bearer b88344cf801c2820ead65a513987d995fffc72cf" "http://localhost:8000/api/v1/workspaces/c72607a7-f11f-41b7-9ac5-a11869bb512c/syncs/"

#get sync with sync_id
curl -o - -v  --header "Content-Type: application/json" --header "Authorization: Bearer b88344cf801c2820ead65a513987d995fffc72cf" "http://localhost:8000/api/v1/workspaces/c72607a7-f11f-41b7-9ac5-a11869bb512c/syncs/aa5ac007-56a3-4c08-b48f-b0508e4de4fe"


# get destinations
curl -X 'GET' \
  'http://localhost:8000/api/v1/workspaces/c72607a7-f11f-41b7-9ac5-a11869bb512c/destinations/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer b88344cf801c2820ead65a513987d995fffc72cf'

#get sources
curl -X 'GET' \
  'http://localhost:8000/api/v1/workspaces/c72607a7-f11f-41b7-9ac5-a11869bb512c/sources/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer b88344cf801c2820ead65a513987d995fffc72cf'
