# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.manage_guest = true

  config.vm.define "datanommer" do |datanommer|
    datanommer.vm.box_url = "https://app.vagrantup.com/centos/boxes/8/versions/2011.0/providers/libvirt.box"
    datanommer.vm.box = "centos/8"
    datanommer.vm.hostname = "datanommer.test"

    datanommer.vm.synced_folder '.', '/vagrant', disabled: true
    datanommer.vm.synced_folder ".", "/home/vagrant/datanommer", type: "sshfs"

    datanommer.vm.provider :libvirt do |libvirt|
      libvirt.cpus = 2
      libvirt.memory = 2048
    end

    datanommer.vm.provision "ansible" do |ansible|
      ansible.playbook = "devel/ansible/datanommer.yml"
      ansible.config_file = "devel/ansible/ansible.cfg"
      ansible.verbose = true
    end
  end

end
