using Microsoft.AspNetCore.Mvc;
using AutoMapper;
using CouchTomato.Core.Repositories;
using CouchTomato.Core.DTOs;
using CouchTomato.Data.Entities;

namespace CouchTomato.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class MoviesController : ControllerBase
{
    private readonly MovieRepository _repo;
    private readonly IMapper _mapper;

    public MoviesController(MovieRepository repo, IMapper mapper)
    {
        _repo = repo;
        _mapper = mapper;
    }

    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var movies = await _repo.GetAllAsync();
        return Ok(_mapper.Map<IEnumerable<MovieDto>>(movies));
    }

    [HttpPost]
    public async Task<IActionResult> Add(MovieDto dto)
    {
        var movie = _mapper.Map<Movie>(dto);
        await _repo.AddAsync(movie);
        return Ok(_mapper.Map<MovieDto>(movie));
    }
}
