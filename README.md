# Automatic Text Marking System for Legal Judgments

## Introduction
- 本專題之目的，乃希望能從法律判決書中提取命名實體（Named Entity）、以及包含判決結果、量刑責度等關鍵詞句，並在使用者介面中以醒目的方式顯示，在為後續研究分析做準備的同時，也能方便使用者閱讀。

## Deploy

- edit .env file,  
`mv .env.sample .env`
- import sample result using 'sample.ipynb'

### Deploy by Docker

- replace `localhost` with `host.docker.internal`
- replace `\` with `^`  in Windows

```
docker run -d -p 7777:11616 \
-e DEBUG=False \
-e NEO4J_SERVER="neo4j" \
-e NEO4J_PASS="adminadmin" \
-e NEO4J_SERVER="http://host.docker.internal:7474" \
--name nlplaw ghcr.io/gdist/nlplaw
```
OR
```
docker run -d -p 7777:11616 --env-file ./.env --name nlplaw ghcr.io/gdist/nlplaw 
```

## Preview