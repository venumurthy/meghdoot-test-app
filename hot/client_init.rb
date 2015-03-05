#!/usr/bin/ruby
#
#Setup chef client.
#

domain_name = ARGV[0]
environment = ARGV[1]
organization = ARGV[2]

fqdn = `curl http://169.254.169.254/latest/meta-data/hostname`.split(".")
node_name = fqdn[0]

system("hostname #{node_name}")
system("domainname #{domain_name}")

ip_address = %x[ifconfig eth0|grep "inet addr"| awk '{print $2}'| cut -d: -f2| tr -d '\n']

#
#Setup Hostname and domainname so chef will work.
#
File.open("/etc/hostname", "w") do |f|
  f.print <<-EOH
#{node_name}
  EOH
end

File.open("/etc/domainname", "w") do |f|
  f.print <<-EOH
#{domain_name}
  EOH
end

File.open("/etc/hosts", "a") do |f|
  f.print <<-EOH
#{ip_address} #{node_name}.#{domain_name} #{node_name}
EOH
end

#
#Setup client.rb file
#
File.open("/var/chef/client.rb", "w") do |f|
        f.print <<-EOH
log_level :info
log_location STDOUT
chef_server_url "https://api.opscode.com/organizations/#{organization}"
validation_client_name "#{organization}-validator"
node_name "#{node_name}.#{domain_name}"
environment "#{environment}"
EOH
end

#
#place chef-client deletion script in /etc/rc0.d
#
File.open("/etc/init.d/remove_chef_client.rb", "w") do |f|
  f.print <<-EOH
#!/usr/bin/ruby
if File.exists?("/etc/chef/client.rb") && File.exists?("/usr/local/bin/chef-client")
  require 'rubygems'
  require 'chef'
  require 'chef/knife'
  require 'chef/knife/node_delete'
  require 'chef/knife/client_delete'

  Chef::Config.from_file("/etc/chef/client.rb")

  nd = Chef::Knife::NodeDelete.new
  nd.name_args = [ Chef::Config[:node_name] ]
  nd.config[:yes] = true
  nd.run

  cd = Chef::Knife::ClientDelete.new
  cd.name_args = [ Chef::Config[:node_name] ]
  cd.config[:yes] = true
  cd.run

  File.unlink("/etc/chef/client.pem")
else
  puts "This node is not connected to Opscode, no need to delete node."
end

exit 0
EOH
end

system("chmod 755 /etc/init.d/remove_chef_client.rb")
system("ln -s /etc/init.d/remove_chef_client.rb /etc/rc0.d/K21remove_chef_client.rb")