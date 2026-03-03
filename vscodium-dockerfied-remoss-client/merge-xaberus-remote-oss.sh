merge() {
  jq '
    if (."enable-proposed-api" | type) != "array" then
      . + {"enable-proposed-api": ["xaberus.remote-oss"]}
    else
      if (."enable-proposed-api" | index("xaberus.remote-oss")) == null then
        ."enable-proposed-api" += ["xaberus.remote-oss"]
      else
        .
      end
    end
  '
}