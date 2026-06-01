#include <bits/stdc++.h>
using namespace std;
int main(){
    freopen("RUTGON.INP","r",stdin);
    freopen("RUTGON.OUT","w",stdout);
    string s; getline(cin,s);
    while(!s.empty() && (s.back()=='\r'||s.back()=='\n')) s.pop_back();
    string r;
    for(char c: s) if(r.empty()||r.back()!=c) r.push_back(c);
    printf("%s\n", r.c_str());
    return 0;
}
