// 64x48 four-bit framebuffer for VGA-style simulation output.
// This is intentionally simulation-friendly rather than synthesis-pure:
// line and rectangle drawing are implemented as tasks for devkit hacking.
module vram(
    input clk,
    input we,
    input [5:0] write_x,
    input [5:0] write_y,
    input [3:0] write_color,
    input [5:0] read_x,
    input [5:0] read_y,
    output [3:0] read_color
);
    localparam W = 64;
    localparam H = 48;
    localparam SIZE = W * H;

    reg [3:0] mem [0:SIZE-1];
    integer i;
    integer dx;
    integer dy;
    integer sx;
    integer sy;
    integer err;
    integer e2;
    integer cx;
    integer cy;

    initial begin
        for (i = 0; i < SIZE; i = i + 1)
            mem[i] = 4'h0;
    end

    always @(posedge clk) begin
        if (we && write_x < W && write_y < H)
            mem[(write_y * W) + write_x] <= write_color;
    end

    assign read_color = (read_x < W && read_y < H) ? mem[(read_y * W) + read_x] : 4'h0;

    task pset;
        input [5:0] x;
        input [5:0] y;
        input [3:0] color;
        begin
            if (x < W && y < H) begin
                mem[(y * W) + x] = color;
                $display("VRAM_PSET x=%0d y=%0d c=%0d", x, y, color);
            end
        end
    endtask

    task clear_all;
        input [3:0] color;
        begin
            for (i = 0; i < SIZE; i = i + 1)
                mem[i] = color;
            $display("VRAM_CLR c=%0d", color);
        end
    endtask

    task draw_line;
        input [5:0] x0;
        input [5:0] y0;
        input [5:0] x1;
        input [5:0] y1;
        input [3:0] color;
        begin
            cx = x0;
            cy = y0;
            dx = (x0 < x1) ? (x1 - x0) : (x0 - x1);
            dy = -((y0 < y1) ? (y1 - y0) : (y0 - y1));
            sx = (x0 < x1) ? 1 : -1;
            sy = (y0 < y1) ? 1 : -1;
            err = dx + dy;

            while (cx != x1 || cy != y1) begin
                pset(cx[5:0], cy[5:0], color);
                e2 = err * 2;
                if (e2 >= dy) begin
                    err = err + dy;
                    cx = cx + sx;
                end
                if (e2 <= dx) begin
                    err = err + dx;
                    cy = cy + sy;
                end
            end
            pset(x1, y1, color);
            $display("VRAM_LINE x0=%0d y0=%0d x1=%0d y1=%0d c=%0d", x0, y0, x1, y1, color);
        end
    endtask

    task draw_rect;
        input [5:0] x;
        input [5:0] y;
        input [5:0] w;
        input [5:0] h;
        input [3:0] color;
        begin
            if (w == 0 || h == 0) begin
                pset(x, y, color);
            end else begin
                draw_line(x, y, x + w - 1, y, color);
                draw_line(x, y + h - 1, x + w - 1, y + h - 1, color);
                draw_line(x, y, x, y + h - 1, color);
                draw_line(x + w - 1, y, x + w - 1, y + h - 1, color);
            end
            $display("VRAM_RECT x=%0d y=%0d w=%0d h=%0d c=%0d", x, y, w, h, color);
        end
    endtask

    task dump_nonzero;
        integer px;
        integer py;
        begin
            for (py = 0; py < H; py = py + 1) begin
                for (px = 0; px < W; px = px + 1) begin
                    if (mem[(py * W) + px] != 4'h0)
                        $display("FB %0d %0d %0d", px, py, mem[(py * W) + px]);
                end
            end
        end
    endtask
endmodule
