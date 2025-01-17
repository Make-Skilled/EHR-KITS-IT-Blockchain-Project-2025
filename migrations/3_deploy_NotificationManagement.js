const NotificationManagement=artifacts.require('NotificationManagement');

module.exports=function(deployer){
    deployer.deploy(NotificationManagement);
}