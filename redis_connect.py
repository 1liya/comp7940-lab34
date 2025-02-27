"""Basic connection example.
"""

import redis

r = redis.Redis(
    host='redis-19787.c81.us-east-1-2.ec2.redns.redis-cloud.com',
    port=19787,
    decode_responses=True,
    username="default",
    password="zKeTTM6rBBVWff08PtBPQehjdoDbcUPk",
)

success = r.set('foo', 'bar')
# True

result = r.get('foo')
print(result)
# >>> bar

# print(r.ping())

# print(r.set("my_name","xuyu")) 
# r.get("my_name")

# print(r.exists("my_name"))
# print(r.exists("random123"))

# r.delete("my_name")
# print( r.exists("my_name"))