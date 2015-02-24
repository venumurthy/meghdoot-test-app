# 
# Cookbook name:: database_server
# Recipe:: default
# To bring up the database server in the meghdoot project

# install mongodb server

package "mongodb" do
    action :install
end

#Change 127.0.0.0 to 0.0.0.0 will bind it to all network interfaces that are available

ruby_block "edit db config file" do
  block do
    rc = Chef::Util::FileEdit.new("/etc/mongodb.conf")
    rc.search_file_replace_line(
    /^bind_ip = 127\.0\.0\.1/,
   "bind_ip = 0.0.0.0"
   )
  rc.write_file
  end
end

# restart service

service "mongodb" do
	action :restart
end
