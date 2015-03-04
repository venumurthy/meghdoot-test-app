#For app server

#Install git
case node[:platform]
  when "debian", "ubuntu"
    package "git-core"
  else
    package "git"
end

#Now installing nodejs

case node["platform"]
  when "ubuntu"
    package "nodejs"
    package "npm"
  when "debian"
    package "nodejs-legacy"
end  

#checkout code from git
git "/home/ubuntu/meghdoot-test-app" do
  repository node["app_server"]["repo"]
  action :sync
  user "ubuntu"
end

bash 'start meghdoo' do
  user 'ubuntu'
  cwd '/home/ubuntu'
  code <<-EOH
  ln -s /usr/bin/nodejs /usr/bin/node
  meghdoot-test-app/node_modules/.bin/forever start meghdoot-test-app/bin/www
  sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 3000
  EOH
end
