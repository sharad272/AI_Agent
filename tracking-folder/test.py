class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
    
    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node
    
    def display(self):
        current = self.head
        while current:
            print(current.data, end=" -> ")
            current = current.next
        print("None")
    
    def delete(self, key):
        if not self.head:
            return
        if self.head.data == key:
            self.head = self.head.next
            return
        current = self.head
        while current.next and current.next.data != key:
            current = current.next
        if current.next:
            current.next = current.next.next

# Example usage
if __name__ == "__main__":
    llist = LinkedList()
    llist.append(1)
    llist.append(2)
    llist.append(3)
    print("Original linked list:")
    llist.display()
    llist.delete(2)
    print("After deleting 2:")
    llist.display()