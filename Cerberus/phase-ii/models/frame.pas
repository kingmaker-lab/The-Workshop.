program CerberusFrame;
{$mode objfpc}
uses SysUtils;

type
  TFrame = array[0..15] of Byte;

procedure Fail(const MessageText: string);
begin
  WriteLn(StdErr, MessageText);
  Halt(64);
end;

function WordValue(const Input: string): LongWord;
var
  Digit: Char;
  Value: QWord;
begin
  if (Length(Input) = 0) or (Length(Input) > 10) then
    Fail('esperado uint32 decimal');
  Value := 0;
  for Digit in Input do
  begin
    if not (Digit in ['0'..'9']) then
      Fail('esperado uint32 decimal');
    Value := (Value * 10) + Ord(Digit) - Ord('0');
  end;
  if Value > High(LongWord) then
    Fail('valor acima de uint32');
  Result := LongWord(Value);
end;

procedure StoreWord(var Frame: TFrame; Offset: Integer; Value: LongWord);
var
  Index: Integer;
begin
  for Index := 0 to 3 do
    Frame[Offset + Index] := Byte((Value shr (Index * 8)) and $FF);
end;

var
  Frame: TFrame;
  OutputFile: File;
  Index, Written: Integer;
  Operation: LongWord;
begin
  if ParamCount <> 4 then
    Fail('uso: frame-pascal admission|recovery A B C');
  case ParamStr(1) of
    'admission': Operation := 1;
    'recovery': Operation := 2;
    else Fail('operação desconhecida');
  end;
  StoreWord(Frame, 0, Operation);
  for Index := 2 to 4 do
    StoreWord(Frame, (Index - 1) * 4, WordValue(ParamStr(Index)));
  Assign(OutputFile, '');
  Rewrite(OutputFile, 1);
  BlockWrite(OutputFile, Frame, SizeOf(Frame), Written);
  Close(OutputFile);
  if Written <> SizeOf(Frame) then
    Halt(74);
end.
