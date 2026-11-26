// AC4: unsigned q=min(63,budget/price), price is the low byte of rs2.
// price=0 returns 0. Six restoring trials, without a general 32-bit divider.
module espino_qcap (
  input wire clk_i, rst_ni, start_i, clear_i,
  input wire [31:0] budget_i,
  input wire [7:0] price_i,
  output reg busy_o, done_o,
  output reg [5:0] result_o
);
  reg [13:0] remainder_q, trial_q;
  reg [5:0] quantity_q, mask_q;
  wire [14:0] difference = {1'b0,remainder_q}-{1'b0,trial_q};
  wire accept_trial = !difference[14];
  always @(posedge clk_i or negedge rst_ni) begin
    if(!rst_ni) begin
      busy_o<=0; done_o<=0; result_o<=0;
      remainder_q<=0; trial_q<=0; quantity_q<=0; mask_q<=0;
    end else begin
      if(clear_i) done_o<=0;
      if(start_i && !busy_o && !done_o) begin
        if(price_i==0) begin result_o<=0; done_o<=1; end
        else if(|budget_i[31:14]) begin result_o<=63; done_o<=1; end
        else begin
          remainder_q<=budget_i[13:0]; trial_q<={1'b0,price_i,5'b0};
          quantity_q<=0; mask_q<=32; busy_o<=1;
        end
      end else if(busy_o) begin
        if(accept_trial) begin
          remainder_q<=difference[13:0]; quantity_q<=quantity_q|mask_q;
        end
        trial_q<={1'b0,trial_q[13:1]}; mask_q<={1'b0,mask_q[5:1]};
        if(mask_q==1) begin
          busy_o<=0; done_o<=1;
          result_o<=quantity_q | (accept_trial ? mask_q : 6'b0);
        end
      end
    end
  end
endmodule
