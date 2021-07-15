# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.manage_guest = true

  config.vm.define "datanommer" do |datanommer|
    datanommer.vm.box_url = "https://download.fedoraproject.org/pub/fedora/linux/releases/34/Cloud/x86_64/images/Fedora-Cloud-Base-Vagrant-34-1.2.x86_64.vagrant-libvirt.box"
    datanommer.vm.box = "f34-cloud-libvirt"
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
