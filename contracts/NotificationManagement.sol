// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract NotificationManagement {
    struct Notification {
        uint notId;           // Unique notification ID
        string notTitle;      // Title of the notification
        string notDescription;// Description of the notification
        string notDate;       // Date of the notification
        uint notTo;           // Recipient's ID (e.g., user ID)
        bool readStatus;      // Read status of the notification
    }

    uint private notificationCounter; // Counter for unique notification IDs
    mapping(uint => Notification[]) private userNotifications; // Maps user ID to their notifications
    event NotificationAdded(uint notId, uint notTo, string notTitle); // Event for notification addition

    constructor() {
        notificationCounter = 0;
    }

    // Add a new notification for a user
    function addNotification(
        string memory notTitle,
        string memory notDescription,
        string memory notDate,
        uint notTo
    ) public {
        require(notTo > 0, "Invalid recipient ID");
        require(bytes(notTitle).length > 0, "Title cannot be empty");
        require(bytes(notDate).length > 0, "Date cannot be empty");

        notificationCounter++;

        Notification memory newNotification = Notification({
            notId: notificationCounter,
            notTitle: notTitle,
            notDescription: notDescription,
            notDate: notDate,
            notTo: notTo,
            readStatus: false
        });

        userNotifications[notTo].push(newNotification);

        emit NotificationAdded(notificationCounter, notTo, notTitle);
    }

    // Retrieve all notifications for a specific user
    function getNotifications(uint userId) public view returns (Notification[] memory) {
        return userNotifications[userId];
    }

    // Mark a specific notification as read
    function markAsRead(uint userId, uint notId) public {
        Notification[] storage notifications = userNotifications[userId];
        for (uint i = 0; i < notifications.length; i++) {
            if (notifications[i].notId == notId) {
                notifications[i].readStatus = true;
                return;
            }
        }
        revert("Notification not found");
    }

    // Retrieve unread notifications for a user
    function getUnreadNotifications(uint userId) public view returns (Notification[] memory) {
        Notification[] storage notifications = userNotifications[userId];
        uint unreadCount = 0;

        // Count unread notifications
        for (uint i = 0; i < notifications.length; i++) {
            if (!notifications[i].readStatus) {
                unreadCount++;
            }
        }

        // Create an array to store unread notifications
        Notification[] memory unreadNotifications = new Notification[](unreadCount);
        uint index = 0;

        // Add unread notifications to the array
        for (uint i = 0; i < notifications.length; i++) {
            if (!notifications[i].readStatus) {
                unreadNotifications[index] = notifications[i];
                index++;
            }
        }

        return unreadNotifications;
    }
}
