FROM ruby:3.3-slim
WORKDIR /app
COPY v0.3/Gemfile ./Gemfile
RUN bundle install --without development test
COPY lib/ ./lib/
COPY v0.3/ ./v0.3/
RUN useradd --uid 10001 --create-home rubyuser
USER 10001:10001
EXPOSE 9292
CMD ["bundle", "exec", "puma", "-C", "v0.3/puma.rb"]
