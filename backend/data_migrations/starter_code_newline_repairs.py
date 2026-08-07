"""7-D4a：字面反斜線換行的 starter code 修補。"""

STARTER_CODE_NEWLINE_REPAIRS = {
    "360f62ca-5748-405c-8eab-2fa96bb5df88": r"""#include <iostream>
#include <string>
using namespace std;

class Student {
public:
    const string Department = "產科學程";
    string Name;
    int Chinese, English, Math;
    int Total;

    void print() {
        // TODO: 輸出成員資料與平均
    }
};

int main() {
    Student S[5];
    for (int i = 0; i < 5; i++) {
        // TODO: 輸入資料、計算總分並呼叫 print()
    }
    return 0;
}
""",
    "af1c4991-7cb0-409f-bc94-b85a459aadfc": r"""#include <iostream>
#include <string>
using namespace std;

class Student {
public:
    string name;
    int chinese, english, math, sum;
    double average;
    void Print();
};

void Student::Print() {
    // TODO: 輸出此物件的成員資料
}

int main() {
    Student s[5];
    for (int i = 0; i < 5; i++) {
        // TODO: 輸入資料並計算 sum 與 average
    }
    for (int i = 0; i < 5; i++) {
        // TODO: 呼叫 s[i].Print()
    }
    return 0;
}
""",
    "d93ee1cf-3bb6-479b-bb50-a37d01d1ac43": r"""#include <iostream>
using namespace std;

int main() {
    double A, B;
    cout << "請輸入A:";
    cin >> A;
    cout << "請輸入B:";
    cin >> B;
    // TODO: 依序輸出 A+B、A-B、A*B、A/B
    return 0;
}
""",
}
