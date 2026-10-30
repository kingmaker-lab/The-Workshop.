bind 'tcp://0.0.0.0:9292'
workers 1
threads 1, 3
environment 'production'
rackup 'v0.3/config.ru'
