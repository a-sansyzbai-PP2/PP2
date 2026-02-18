class Father:
    def skill_father(self):
        print("Father skill")

class Mother:
    def skill_mother(self):
        print("Mother skill")

class Child(Father, Mother):
    pass
c = Child()
c.skill_father()
c.skill_mother()